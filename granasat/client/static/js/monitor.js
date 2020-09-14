var monitor = function(){
    var charts = {
        'cpu-temp': {'title': 'CPU Temp', 'chart': null, unit: '°', colors: {
            'degrees': '#d39e00'
        }},
        'camera-temp': {'title': 'Camera Temp', 'chart': null, unit: '°', colors: {
            'degrees': '#d39e00'
        }},
        'magnetometer': {'title': 'Magnetometer', 'chart': null, unit: ' μT', colors: {
            'x': '#dc3545', 'y': '#1e7e34', 'z': '#0062cc'
        }},
        'accelerometer': {'title': 'Accelerometer', 'chart': null, unit: ' m/s^2', colors: {
            'x': '#dc3545', 'y': '#1e7e34', 'z': '#0062cc'
        }}
    };

    // Initialize the charts
    $.each(charts, function(index, value){
        var chart = createChart(index, value.title, value.unit);
        charts[index]['chart'] = chart;
    });

    // Bindings
    // Metrics dropdown li
    $('.dropdown-metrics li').on('click', function(){
        $('#btn-metrics').html($(this).text());
        $('#btn-metrics').val($(this).val());
    });

    // Metrics refresh
    $('#btn-refresh-metrics').click(function(){
        minutes = parseInt($('#btn-metrics').val());
        refreshMetrics(charts, minutes);
    });

    // Initial trigger
    $('#btn-refresh-metrics').trigger('click');
};

/**
 * Create a chart.
 *
 * @param {String} name chat's name.
 * @param {String} title title's to show in the chart.
 * @param {String} unit unit to show in the tooltip.
 *
 * @return {Function} **update()** the chart with new data.
 */
function createChart(name, title, unit) {
    var ctx = $('#chart-' + name);
    var chart = new Chart(ctx, {
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
                intersect: false,
                callbacks: {
                    label: function(tooltipItems, data) {
                        return data.datasets[tooltipItems.datasetIndex].label + ': ' + tooltipItems.yLabel + unit;
                    }
                }
            },
            elements: {
                line: {
                    borderWidth: 3,
                    fill: false
                },
                point: {
                    radius: 0
                }
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                }],
                yAxes: [{
                    display: true,
                    ticks: {
                        suggestedMin: 30,
                        suggestedMax: 45
                    }
                }]
            }
        }
    });

    function update(datasets) {
        chart.data = datasets;
        chart.update({
            duration: 800,
            easing: 'easeOutBounce'
        });
    };

    return update;
};

/**
 * Request metrics of the last minutes given as argument and update the charts
 * given as argument.
 *
 * @param {String} charts chat's name.
 * @param {String} minutes title's to show in the chart.
 */
function refreshMetrics(charts, minutes){
    $.ajax({
        url: "/get-metrics/" + minutes,
        success: function(data){
            $.each(data, function(metric, series){
                datasets = {
                    labels: [],
                    datasets: []
                };
                setsdict = {};
                $.each(series, function(index, serie){
                    $.each(serie, function(k, value){
                        if (k == "time"){
                            datasets.labels.push(value.replace('Z','').replace('T', ' '));
                        } else {
                            if (!(k in setsdict)){
                                setsdict[k] = [];
                            };
                            setsdict[k].push(value);
                        };
                    });
                });
                $.each(setsdict, function(label, serie){
                    datasets.datasets.push({
                        label: label,
                        data: serie,
                        borderColor: charts[metric].colors[label]
                    });
                });
                charts[metric].chart(datasets);
            });
        },
        cache: false,
        type: "get"
    });
};
