$(document).ready(function() {
    $('.dropdown.item')
      .popup({
        inline     : true,
        hoverable  : true,
        position   : 'bottom left',
        delay: {
          show: 300,
          hide: 800
        }
      })
    ;
    $('.ui.dropdown').dropdown();
    $('.ui.accordion').accordion();
  
    
  });