var charts = function(){
    // Ajax query to flask endpoint
    // Will recieve a list of dicts
    // Create two variables like...
    // var labels
    // var points
    // for item in data:
    // labels.append(item.time)
    // points.append(item.value)
    var labels;
    var points;


    var ctx = $('#chart-cpu-temp');
    cpuTemp = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'CPU Temp',
                data: points,
            }]
        },
        options: {
        }
    });
};
