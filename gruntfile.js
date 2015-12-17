module.exports = function(grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        uglify: {
            options: {
                banner: '/*! <%= pkg.name %> <%= grunt.template.today("yyyy-mm-dd") %> */\n'
            }
        },
        concat: {
            assets: {
                src: [
                    'bower_components/ol3/build/ol.js',
                    'bower_components/ol3-layerswitcher/src/ol3-layerswitcher.js',
                    'bower_components/angular-loading-bar/build/loading-bar.min.js',
                    'bower_components/angular-openlayers-directive/dist/angular-openlayers-directive.min.js',
                ],
                dest: 'ogcbrowser/base/static/js/ogcbrowser-assets.js'
            }
        },
        cssmin: {
            assets: {
                src: [
                    'bower_components/angular-loading-bar/build/loading-bar.min.css',
                    'bower_components/ol3/css/ol.css',
                    'bower_components/ol3-layerswitcher/src/ol3-layerswitcher.css'
                ],
                dest: 'ogcbrowser/base/static/css/ogcbrowser-assets.css'
            }
        },
        less: {
            development: {
                files: [
                    {
                        'geosk/css/site_base.css': 'geosk/less/site_base.less'
                    }
                ]
            },
            production: {
                files: [
                    {
                        'geosk/css/site_base.css': 'geosk/less/base.less'
                    }
                ]
            }
        }
    });


  // Load the plugin that provides the "uglify" task.
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-text-replace');


  // Default task(s).
    grunt.registerTask('default', ['uglify']);

};
