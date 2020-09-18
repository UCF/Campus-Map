const gulp     = require('gulp');
const cleanCss = require('gulp-clean-css');
const uglify   = require('gulp-uglify');
const rename   = require('gulp-rename');

const config = {
  src: {
    'cssPath': './static_files/style',
    'jsPath': './static_files/js'
  },
  dist: {
    'cssPath': './static_files/style',
    'jsPath': './static_files/js'
  }
};

gulp.task('js', () => {
  return gulp.src(`${config.src.jsPath}/map.js`)
    .pipe(uglify())
    .pipe(rename({
      extname: '.min.js'
    }))
    .pipe(gulp.dest(config.dist.jsPath));
});

gulp.task('default', gulp.series('js'));
