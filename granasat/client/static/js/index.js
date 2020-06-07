var bootstrap = function(){
    // Camera
    camera();
    // Monitor
    monitor();

    // Enable tooltips everywhere
    $('[data-toggle="tooltip"]').tooltip();

    // var refreshInterval = 15000;
    // getMonitorData();

    // function getMonitorData(){
    //     $.ajax({
    //         url: "/get-monitor-data", success: function(data){
    //             $.each(data, function(key, value){
    //                 $('#monitor-' + key).html(value);
    //             });
    //         },
    //         cache: false,
    //         complete: function() {
    //             setTimeout(getMonitorData, refreshInterval);
    //         }
    //     });
    // };
};

window.onload = bootstrap;
