var startracker = function(){
    // Create grayscale image histogram as a Chart
    var hist_chart = createHistChart($('#chart-histogram'), "Grayscale Histogram");

    // Process image binding
    $("#btn-process-image").on('click', function(){
        processImage(hist_chart);
    });

    // Image upload binding
    $("#btn-upload-image").click(uploadImage);
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
            console.log('Uploading....');
        },
        success: function(data){
            $("#btn-upload-image-close").click();
            $("#img-frame").attr("src", "data:image/jpeg;base64," + data.b64_img);
            $("#img-frame").attr("data-uuid", data.uuid);
            $('#frame-tab').click();
        }
    });
};


function processImage(hist_chart){
    console.log("Processing image");
    imageUUID = $('#img-frame').attr('data-uuid');
    if (imageUUID === undefined) {
        console.log("There is no image to process.");
        return;
    }
    $.ajax({
        url: "/process-image",
        beforeSend: function() {
            // Show loader
            showFrameLoader();
            $('#logs').empty();
            // Disable buttons
            $('#btn-process-image').prop("disabled", true);
            $('#btn-upload-show-modal').prop("disabled", true);
        },
        success: function(data){
            // Update histogram data
            datasets = {
                labels: [],
                datasets: []
            };
            values = [];
            $.each(data.hist, function(index, value){
                datasets.labels.push(index);
                values.push(value[0]);
            });
            datasets.datasets.push({
                label: "number of pixels",
                data: values,
                borderColor: "blue"
            });
            var max = Math.max.apply(null, values);
            hist_chart(datasets, max);
            // Set thresholded image
            $("#img-threshold").attr("src","data:image/jpeg;base64," + data.b64_thresh_img);

            // If a solution was found draw pattern points
            if (data.pattern == true){
                $("#img-pattern").attr("src","data:image/jpeg;base64," + data.pattern_points);
            }

            // Show report in Results section
            //   Pattern found?
            if (data.results.pattern.type == 'success'){
                html = '<div><span class="badge badge-success">Success</span>';
                html += '<span class="font-weight-bold"> ' +  data.results.pattern.msg + '</span></div>';
                $('#pattern-tab').click();
            } else {
                html = '<div><span class="badge badge-danger">Error</span>';
                html += '<span class="font-weight-bold"> ' +  data.results.pattern.msg + '</span></div>';
                $('#frame-tab').click();
            }
            $('#logs').append(html);
            // Threshold selected
            html = '<div><span class="badge badge-info">Info</span>';
            html += '<span class="font-weight-bold"> ' +  data.results.threshold.msg + '</span></div>';
            $('#logs').append(html);
            // Total stars found in the image
            html = '<div><span class="badge badge-info">Info</span>';
            html += '<span class="font-weight-bold"> ' +  data.results.stars.msg + '</span></div>';
            $('#logs').append(html);
            if (data.results.labeled) {
                html = '<div><span class="badge badge-info">Info</span>';
                html += '<span class="font-weight-bold"> ' +  data.results.labeled.msg + '</span></div>';
                $('#logs').append(html);
            }
        },
        complete: function(){
            $('.loader').hide();
            $('#btn-process-image').prop("disabled", false);
            $('#btn-upload-show-modal').prop("disabled", false);
        },
        cache: false,
        data: {
            uuid: imageUUID,
            auto_threshold: $('#auto-threshold').is(':checked'),
            label_guide_stars: $('#label-guide-stars').is(':checked'),
            threshold: $('#threshold').val()
        },
        type: "get"
    });
};

/**
 * Create histogram chart.
 *
 * @param {String} canvasID ID of the canvas.
 * @param {String} title Title for the chart.
 */

function createHistChart(canvas, title) {
    var chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: [],
                data: [],
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: title
            },
            legend: {
                display: false,
            },
            tooltips: {
                mode: 'index',
                intersect: false
            },
            elements: {
                line: {
                    // tension: 0.9,
                    borderWidth: 2,
                    fill: false
                },
                point: {
                    radius: 0
                }
            },
            scales: {
                xAxes: [{
                    display: true,
                    ticks: {
                        suggestedMin: 0,
                        step: 5,
                        suggestedMax: 256
                    }
                }],
                yAxes: [{
                    display: true,
                    ticks: {
                        suggestedMin: 0,
                        suggestedMax: 2000000
                    }
                }]
            }
        }
    });

    function update(datasets, maxSuggested) {
        chart.data = datasets;
        chart.options.scales.yAxes[0].ticks.suggestedMax = maxSuggested;
        chart.update({
            duration: 800,
            easing: 'easeOutBounce'
        });
    };

    return update;
};
