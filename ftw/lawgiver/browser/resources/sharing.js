jQuery(function($){

  var strip_url_params = function () {
    var index = 0,
        url = location.href;
    index = url.indexOf('?');
    if(index == -1){
        index = url.indexOf('#');
    }
    if(index != -1){
        url = url.substring(0, index);
    }
    return url;
  };

  var setup_overlay = function() {
    var $elem = $(this);
    var role = $.trim($elem.text());
    var url = strip_url_params().concat(
        '/lawgiver-sharing-describe-role?role='.concat(
            encodeURIComponent(role)));
    var $link = $('<a>', {
      text: role,
      href: url});
    $elem.html($link);

    $link.prepOverlay({
      subtype: 'ajax',
      noform: function(el) {return $.plonepopups.noformerrorshow(el, 'close');}
    });
  };

  $('body.template-sharing').find('table#current-user-group-sharing th').slice(1).each(setup_overlay);
  $('body.template-sharing').find('table#user-group-sharing th').slice(1).each(setup_overlay);
  if ($('.tabbedview-tabs #tab-participants')) {
    $(document).ajaxComplete(function() {
      $('#participants_overview td.roleNames span.roleName').each(setup_overlay);
    });
  }

});
