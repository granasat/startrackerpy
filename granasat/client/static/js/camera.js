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

    // Image upload binding
    $("#btn-upload-image").click(uploadImage);

    // Queue burst binding
    $("#btn-queue-burst").click(queueBurst);

    // Get camera parameters
    getCameraParams();

    // Get bursts
    getBursts();
};

/**
 * Upload a custom user image.
 */
function uploadImage(){
    var frmdata = new FormData();
    var file = $('#upload-file-input')[0].files[0];
    frmdata.append('image', file);

    $.ajax({
        url: "/upload-image",
        type: "post",
        data: frmdata,
        contentType: false,
        processData: false,
        cache: false,
        beforeSend: function(){
            // Uploading gif?
            console.log('Uploading....');
        },
        success: function(data){
            $("#btn-upload-image-close").click();
            $("#img-frame").attr("src","data:image/jpeg;base64," + data.b64_img);
            $("#img-frame").attr("data-uuid", data.uuid);
        }
    });
};

/**
 * Get a frame and update the main image element with its data.
 */
function getFrame(){
    $.ajax({
        url: "/current-frame",
        success: function(data){
            // Brightness to 1
            $("#img-frame").css({filter: "brightness(1)"});
            $("#img-frame").attr("src","data:image/jpeg;base64," + data.b64_img);
            $("#img-frame").attr("data-uuid", data.uuid);
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

/**
 * Get current camera parameters and update the DOM with their values.
 */
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

/**
 * Get the list of bursts and update the DOM.
 */
function getBursts(){
    $.ajax({
        url: "/get-bursts",
        success: function(data){
            $("#table-bursts > tbody").html(data);
        },
        cache: false,
        type: "get"
    });
};

/**
 * Download a burst.
 *
 * @param {Number} burstId ID of the burst to be downloaded.
 * @param {String} format Valid formats are: raw, jpeg or matlab.
 */
function downloadBurst(burstId, format){
    window.location = `download-burst?burstId=${burstId}&format=${format}`;
};

/**
 * Delete a burst.
 *
 * @param {Number} burstId ID of the burst to be deleted.
 */
function deleteBurst(burstId){
    $.ajax({
        url: "/delete-burst",
        success: function(){
            getBursts();
        },
        cache: false,
        data: {
            burstId: burstId
        },
        type: "get"
    });
};


/**
 * Queue a burst, reading the current camera values from the DOM.
 */
function queueBurst(){
    $.ajax({
        url: "/queue-burst",
        success: function(){
            getBursts();
        },
        cache: false,
        data: {
            duration: $('#input-duration').val(),
            interval: $('#input-interval').val(),
            brightness: $("#brightness-input").val(),
            gamma: $("#gamma-input").val(),
            gain: $("#gain-input").val(),
            exposure: $("#exposure-input").val()
        },
        type: "get"
    });
};
