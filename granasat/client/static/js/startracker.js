var startracker = function(){
    // Create grayscale image histogram as a Chart
    var hist_chart = createHistChart($('#chart-histogram'), "Grayscale Histogram");

    // Process image binding
    $("#btn-process-image").on('click', function(){
        processImage(hist_chart);
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
            // If a solution was found draw pattern points
            if (data.pattern == true){
                $("#img-pattern").attr("src","data:image/jpeg;base64," + data.pattern_points);
            }
            $('#pattern-tab').click();
        },
        cache: false,
        data: {
            uuid: imageUUID
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
