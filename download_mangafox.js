manga = require('./manga.js')
async = require('async')
_ = require('underscore')

_.each(process.argv.slice(2), function(mangaurl) {
    var pending = manga.scrapeChapterList(mangaurl);
    pending.on('done', function() {console.log('done!');})
    var check = function() {
        if (!pending.isDone()) {
            console.log('sleeping ' + JSON.stringify(pending.counter));
            _.delay(check, 5000);
        }
    }
    check();
});
