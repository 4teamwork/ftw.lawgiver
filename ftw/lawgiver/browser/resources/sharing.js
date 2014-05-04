jQuery(function($){

  $('body.template-sharing').
      find('table#user-group-sharing th, table#current-user-group-sharing th').slice(1).each(function() {
        var $th = $(this);
        var role = $.trim($th.text());
        var $link = $('<a>', {
          text: role,
          href: 'lawgiver-sharing-describe-role?role='.concat(
              encodeURIComponent(role))});
        $th.text('');
        $link.appendTo($th);

        $link.prepOverlay({
          subtype: 'ajax',
          noform: function(el) {return $.plonepopups.noformerrorshow(el, 'close');}
        });

      });

});
