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

    // Queue burst binding
    $("#btn-queue-burst").click(queueBurst);

    // Get camera parameters
    getCameraParams();

    // Get bursts
    getBursts();
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
            // Show loader
            showFrameLoader();
        },
        complete: function(){
            $('.loader').hide();
            $('#btn-frame').removeClass('active');
            $('#frame-tab').click();
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

function showFrameLoader(){
    if ($('#frame').hasClass('active')){
        parent = $('#frame');
    } else if($('#histogram').hasClass('active')){
        parent = $('#histogram');
    } else if($('#thresholded').hasClass('active')){
        parent = $('#thresholded');
    } else if($('#pattern').hasClass('active')){
        parent = $('#pattern');
    } else {
        return;
    }
    ewidth = parseInt(parent.css("width").replace("px"),"");
    eheight = parseInt(parent.css("height").replace("px"),"");
    loaderWidth = parseInt($('.loader').css("width").replace("px"),"");
    loaderHeight = parseInt($('.loader').css("height").replace("px"),"");
    lleft = (ewidth / 2 - loaderWidth / 2) + "px";
    ltop = (eheight / 2 - loaderHeight / 2) + "px";
    console.log(ewidth);
    console.log(eheight);
    console.log(lleft);
    console.log(ltop);
    $('.loader').css({
        position: 'absolute',
        zIndex: 5000,
        left: lleft,
        top: ltop
    }).show();
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
 * @param {String} format Valid formats are: raw or jpeg.
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
