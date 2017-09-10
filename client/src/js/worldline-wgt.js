import {makeCalendar, updateFeed} from "wlp-calendar";
import {makeTimeline, resetTimelineSpan, addFeed} from "wlp-timeline";
import {select} from "d3-selection";
import {csv} from "d3-request";


function buildApp(domElementID) {

    select(domElementID).append('div')
        .attr('id', 'divTimeline');
    select(domElementID).append('div')
        .attr('id', 'divCalendar');

    makeTimeline("#divTimeline", 815, 500, feed => {
        updateFeed(feed);
    });

    const weightData = [];
    const weightTrendData = [];
    const caloriesData = [];
    const caloriesTrendData = [];
    const stepsData = [];
    const stepsTrendData = [];

    csv('./fitness_data.csv', function (error, data) {

        data.forEach(function (d) {
            let tempdate = new Date(d['Date']);
                tempdate.setHours(tempdate.getHours() + 12 + tempdate.getTimezoneOffset()/60.0);
            let tempdate2 = new Date(tempdate.toString());
            weightData.push({'timestamp': tempdate2, 'measurementValue': Number(d['Weight'])});
            weightTrendData.push({'timestamp': tempdate2, 'measurementValue': Number(d['WeightSmoothed5Days'])});
            caloriesData.push({'timestamp': tempdate2, 'measurementValue': Number(d['Calories'])});
            caloriesTrendData.push({'timestamp': tempdate2, 'measurementValue': Number(d['CaloriesSmoothed5Days'])});
            stepsData.push({'timestamp': tempdate2, 'measurementValue': Number(d['Steps'])});
            stepsTrendData.push({'timestamp': tempdate2, 'measurementValue': Number(d['StepsSmoothed5Days'])});
        });

        addFeed({
            'feedInfo': {
                'feedId': 'steps',
                'measurementLabel': 'Steps',
                'measurementTimespan': 1,
                'measurementMinimum': 5000,
                'measurementMaximum': 20000
            },
            'data': stepsData,
            'trendData': stepsTrendData
        });
        addFeed({
            'feedInfo': {
                'feedId': 'calories',
                'measurementLabel': 'Calories',
                'measurementTimespan': 1,
                'measurementMinimum': 1500,
                'measurementMaximum': 3000
            },
            'data': caloriesData,
            'trendData': caloriesTrendData
        });
        addFeed({
            'feedInfo': {
                'feedId': 'weight',
                'measurementLabel': 'Weight',
                'measurementTimespan': 1,
                'measurementMinimum': 160,
                'measurementMaximum': 180,
            },
            'data': weightData,
            'trendData': weightTrendData
        });

        makeCalendar('#divCalendar', 800, [2013, 2017], dateSpan => {
            resetTimelineSpan(dateSpan);
        });

        let date1 = new Date();
        date1.setMonth(date1.getMonth() - 6);
        let date2 = new Date();
        date2.setMonth(date2.getMonth() + 3);
        resetTimelineSpan([date1, date2]);

        // updateFeed({
        //     'feedInfo': {
        //         'feedId': 'weight',
        //         'measurementLabel': 'Weight',
        //         'measurementTimespan': 1,
        //         'measurementMinimum': 160,
        //         'measurementMaximum': 185
        //     },
        //     'data': weightData,
        // });

    });


}


export {buildApp};

