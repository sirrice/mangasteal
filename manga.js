var async = require('async')
var $ = require('jquery')
var net = require('net')
var http = require('http')
var _ = require('underscore')
var url = require('url')
var fs = require('fs')
var events = require('events')

var sum = function(a,b) {return a+b;};
var identity = function(x){return x;};
var printarg = function(x){console.log(x);return x;}
var pad = function(s, ndigits) {
    ndigis = ndigits || 3;
    var pad = "00000000000000";
    return pad.substring(0, Math.min(ndigits, pad.length) - s.length) + s;
}


var Pending = function() {
    this.counter = {};
}
_.extend(Pending.prototype, events.EventEmitter.prototype, {
    isDone: function() {
        return _.reduce(_.values(this.counter), sum, 0) == 0;
    },
    update: function(key, v) {
        if (!this.counter[key]) {
            this.counter[key] = 0;
        }
        this.counter[key] += v;
        return this.counter[key];
    },
    inc: function(key) {
         return this.update(key, 1);
    },
    dec: function(key) {
        if (this.update(key, -1) == 0) {
            this.emit('done')
            return this.isDone();
        }
     }
})



var http_request = function(task, cb) {
    var fullurl = task.fullurl;
    var encoding = task.encoding? task.encoding : null;
    if (!fullurl) {
        return
    }
    console.log("http_request: " + fullurl);

    var request_opts = {
        hostname : url.parse(fullurl).hostname,
        port : 80,
        path : url.parse(fullurl).path,
        method : 'GET'
    }

    var handler = function(res) {
        if (encoding) {
            res.setEncoding(encoding);
        }

        var data = '';
        res.on('data', function(chunk) {
            data += chunk;
        });
        res.on('end', function() {
            try {
                if (encoding == 'binary') {
                    cb(data);
                } else {
                    cb($(data))
                }
            } catch(err) {
                console.log('ERR: ' + err);
                cb(null);
            }
        });
        res.on('error', function(err) {
            console.log('ERR: ' + err);
            cb(null);
        });
    }

    var req = http.request(request_opts, handler);
    req.on('error', function(err) {
        cb(null);
        console.log('ERR: ' + fullurl + '\nERR: ' + err.message);
    });
    req.end()
}

var Requester = function(concurrent) {
    this.concurrent = concurrent;
    this.q = async.queue(http_request, concurrent);
}
_.extend(Requester.prototype, events.EventEmitter.prototype, {
    call: function(task, cb) {
          this.q.push(task, cb);
          console.log('req_q: ' + this.q.length());
    }
});



var page_requester = new Requester(2);
var img_requester = new Requester(5);



var row_not_exists = function(title, date, cb) {
    var query = 'select count(*) as count from posts where title = $1 and date = $2'
    var res = db.query(query, [title, date]);
    res.on('row', function(row) {
        if (row.count == 0) {
            cb()
        }
    })
}


var getImageSrc = function(dom) {
    var imageSrc = dom.find('#image').attr('src');
    return imageSrc;
}

var getPageLinks = function(dom) {
    var options = dom.find("#top_bar .l  select > option");
    var pages = options.map(function(idx, el) {
        var pid = $(el).val();
        return pid + '.html';
    });
    return pages;
}

var getChapterLinks = function(dom) {
    var slides = dom.find(".slide").next();
    var tips = slides.find("li a.tips");
    return _.map(tips, function(el){  return $(el).attr('href')})
}

var chapterMetadata = function(theurl) {
    var p = url.parse(theurl);
    var folders = p.path.split('/').filter(identity);
    if (folders.length <= 2) {
        return null;
    }
    fsfolders = folders.slice(1,folders.length-1);

    return {
        manga:folders[1],
        folders: fsfolders,
        fspath: fsfolders.join('/'),
        path:folders.slice(0, folders.length-1).join('/'),
        fullpath: [p.protocol, '', p.hostname].concat(folders.slice(0, folders.length-1)).join('/')
    };
}


var ensurePathSync = function(folders) {
    for (var i = 1; i <= folders.length; i++) {
        var path = folders.slice(0, i).join('/');
        if (!fs.existsSync(path)) {
            fs.mkdirSync(path);
        }
    }
    return true;
}
ensurePathSync = _.memoize(ensurePathSync);


var scrapeChapterList = function(link) {
    var pending = new Pending();
    pending.inc('manga');
    page_requester.call({fullurl:link},
            _.bind(procChapterList, {}, {pending:pending}));
    return pending;
}
var procChapterList = function(opts, dom) {
    _.each(getChapterLinks(dom), function(url, idx) {
        var md = chapterMetadata(url);
        var newopts = _.extend(_.clone(opts), md)
        if (md && idx > 9) {
            console.log('downloading chapter: ' + url);
            newopts.pending.inc('chapter');
            page_requester.call({fullurl:url}, _.bind(procChapter, {}, newopts));
        }
    });
    opts.pending.dec('manga');
}

var procChapter = function(opts, dom) {
    var path = opts.fullpath;
    var pages = getPageLinks(dom);
    console.log('procChapter: ' + opts);

    ensurePathSync(opts.folders);
    _.each(pages, function(page, idx) {
        var pageurl = path + '/' + page;
        var newopts = _.extend(_.clone(opts), {
            fname : opts.fspath + '/' + pad(''+idx, 3) + ".jpg"
        });
        newopts.pending.inc('page');
        page_requester.call({fullurl:pageurl}, _.bind(procPage, {}, newopts));
    });
    opts.pending.dec('chapter');
}

var procPage = function(opts, dom) {
    if (!dom) {
        opts.pending.dec('page');
        return;
    }
    var url = getImageSrc(dom);
    console.log('procPage: ' + opts.fullpath + '\t' + opts.fname);
    if (!url || fs.existsSync(opts.fname)) {
        opts.pending.dec('page');
        return;
    }

    var save = function(data) {
        opts.pending.dec('page');
        if (!data) {
            return;
        }
        fs.writeFileSync(opts.fname, data, 'binary', function(err) {
            if (err) throw err;
            console.log('saved ' + opts.fname)
        })
    }

    img_requester.call({fullurl:url, encoding:'binary'}, save);
}



//db = new pg.Client(conStr);
//db.connect();
//
exports.scrapeChapterList = scrapeChapterList;


