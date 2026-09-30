module.exports = {
    content: [
        "_site/**/*.html",
        "_site/**/*.js"
    ],
    css: [
        "_site/assets/css/*.css"
    ],
    output: "_site/assets/css/",
    skippedContentGlobs: [
        "_site/assets/**/*.html"
    ],
    // classes toggled from JavaScript, which purgecss cannot see in the HTML
    safelist: ["pub-hidden", "active", "table-dark", "open", "transition"]
};
