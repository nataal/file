var App = (function () {
  'use strict';
  
  App.pageCalendar = function( ){


    /* initialize the external events
    -----------------------------------------------------------------*/

    $('#external-events .external-event').each(function() {

      // store data so the calendar knows to render an event upon drop
      $(this).data('event', {
        title: $.trim($(this).text()), // use the element's text as the event title
        stick: true // maintain when user navigates (see docs on the renderEvent method)
      });

      // make the event draggable using jQuery UI
      $(this).draggable({
        zIndex: 999,
        revert: true,      // will cause the event to go back to its
        revertDuration: 0  //  original position after the drag
      });

    });

    var date = new Date();
    var d = date.getDate();
    var m = date.getMonth();
    var y = date.getFullYear();


    /* initialize the calendar
    -----------------------------------------------------------------*/

    $('#calendar').fullCalendar({
      header: {
        left: 'title',
        center: '',
        right: 'month,agendaWeek,agendaDay, today, prev,next',
      },
      defaultDate: date,
      editable: true,
      eventLimit: true,
      droppable: true, // this allows things to be dropped onto the calendar
      drop: function() {
        // is the "remove after drop" checkbox checked?
        if ($('#drop-remove').is(':checked')) {
          // if so, remove the element from the "Draggable Events" list
          $(this).remove();
        }
      },
      events: [
        {
          title: 'All Day Event',
          start: new Date(y, m, d-1)
        },
        {
          title: 'Long Event',
          start: new Date(y, m, d-5),
          end: new Date(y, m, d-1)
        },
        {
          id: 999,
          title: 'Repeating Event',
          start: new Date(y, m, d-3, 16, 0),
          allDay: false
        },
        {
          id: 999,
          title: 'Repeating Event',
          start: new Date(y, m, d+4, 16, 0),
          allDay: false
        },
        {
          title: 'Meeting',
          start: new Date(y, m, d, 10, 30),
          allDay: false
        },
        {
          title: 'Lunch',
          start: new Date(y, m, d, 12, 0),
          end: new Date(y, m, d, 14, 0),
          allDay: false
        },
        {
          title: 'Birthday Party',
          start: new Date(y, m, d+1, 19, 0),
          end: new Date(y, m, d+1, 22, 30),
          allDay: false
        },
        {
          title: 'Click for Google',
          start: new Date(y, m, 28),
          end: new Date(y, m, 30),
          url: 'http://google.com/'
        }
      ]
    });

    //Skycons
    function widget_weather(){
      var widgetEl = $(".widget-weather");
      var skycons = new Skycons({"color": "#555555"});
      skycons.add($(".icon1", widgetEl)[0], Skycons.CLEAR_DAY);
      skycons.add($(".icon2", widgetEl)[0], Skycons.PARTLY_CLOUDY_DAY);
      skycons.add($(".icon3", widgetEl)[0], Skycons.RAIN);
      skycons.play();
    }

    widget_weather();

  };

  return App;
})(App || {});
