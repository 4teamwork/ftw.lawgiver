jQuery(function($){

  var setup_overlay = function() {
    var $th = $(this);
    var role = $.trim($th.text());
    var url = location.href.concat(
        '/lawgiver-sharing-describe-role?role='.concat(
            encodeURIComponent(role)));
    var $link = $('<a>', {
      text: role,
      href: url});
    $th.html($link);

    $link.prepOverlay({
      subtype: 'ajax',
      noform: function(el) {return $.plonepopups.noformerrorshow(el, 'close');}
    });
  };

  $('body.template-sharing').find('table#current-user-group-sharing th').slice(1).each(setup_overlay);
  $('body.template-sharing').find('table#user-group-sharing th').slice(1).each(setup_overlay);

});
