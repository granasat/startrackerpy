var camera = function(){
    // Bindings parameters
    $("#brightness-input").on('input', function(){
        $("#brightness-value").html($("#brightness-input").val());
    });
    $("#gamma-input").on('input', function(){
        $("#gamma-value").html($("#gamma-input").val());
    });
    $("#gain-input").on('input', function(){
        $("#gain-value").html($("#gain-input").val());
    });
    $("#exposure-input").on('input', function(){
        $("#exposure-value").html($("#exposure-input").val());
    });

    // Get frame binding
    $("#btn-frame").click(getFrame);

    // Get camera parameters
    getCameraParams();
};


// Helper functions
function getFrame(){
    $.ajax({
        url: "/current-frame",
        success: function(data){
            // Brightness to 1
            $("#img-frame").css({filter: "brightness(1)"});
            $("#img-frame").attr("src","data:image/jpeg;base64," + data.b64_img);
            matlab_data = data.matlab;
            $("#btn-matlab").removeClass('disabled');
        },
        beforeSend: function(){
            // Brightness to 0.25
            $("#img-frame").css({filter: "brightness(0.25)"});
            // Compute elements positions to center the loader
            ewidth = parseInt($('.frame').css("width").replace("px"),"");
            eheight = parseInt($('.frame').css("height").replace("px"),"");
            loaderWidth = parseInt($('.loader').css("width").replace("px"),"");
            loaderHeight = parseInt($('.loader').css("height").replace("px"),"");
            lleft = (ewidth / 2 - loaderWidth / 2) + "px";
            ltop = (eheight / 2 - loaderHeight / 2) + "px";
            $('.loader').css({
                position: 'absolute',
                zIndex: 5000,
                left: lleft,
                top: ltop
            }).show();
        },
        complete: function(){
            $('.loader').hide();
            $('#btn-frame').removeClass('active');
        },
        cache: false,
        data: {
            brightness: $("#brightness-input").val(),
            gamma: $("#gamma-input").val(),
            gain: $("#gain-input").val(),
            exposure: $("#exposure-input").val()
        },
        type: "get"
    });
};

// Ajax call to get the current parameters of the camera.
function getCameraParams(){
        $.ajax({
            url: "/get-camera-params",
            success: function(data){
                $.each(data, function(key, value){
                    $("#" + key + "-input").val(value);
                    $("#" + key + "-value").html(value);
                });
            },
            cache: false
        });
    };
