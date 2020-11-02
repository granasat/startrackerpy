var bootstrap = function(){
    // Camera
    camera();
    // Monitor
    monitor();

    // Startracker
    startracker();

    // Enable tooltips everywhere
    $('[data-toggle="tooltip"]').tooltip();
};

window.onload = bootstrap;
