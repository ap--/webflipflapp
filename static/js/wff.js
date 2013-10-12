
function loadSpreadsheet( ssid, ssname ) {
    $.get('/spreadsheet', { 'ssid': ssid, 'ssname': ssname }, function(data) {
        var html = jQuery('<div>').html(data);
        var header = html.find('.breadcrumb');
        var boxes = html.find('.thumbnails');
        $('#wff-boxes-spreadsheet-heading-' + ssid + " ul" ).replaceWith(header);
        $('#wff-boxes-spreadsheet-container-' + ssid).append(boxes);
    });
}



function generateHeader( ssid, boxname, N ) {
    var Header = "";
    Header += "<div class='wff-boxes-calendar-container wff-minimized'>";
    Header += "<p><span><strong><a onclick='viewBox(\""+ssid+"\","+N+")'>"+boxname+"</a></strong></span>";
    Header += "<span>scheduled:</span>";
    Header += "</div>"
    return Header;
}

function viewBox( ssid, N ) {
    $("#box-header-" + ssid + "-" + N).toggleClass('wff-minimized');
    $("#box-data-" + ssid + "-" + N).toggle('fast');
    $(".footable").resize();
}

function viewAllBoxes( ssid, N ) {
    for (var i=0;i<N;i++) {
        viewBox( ssid, i );
    };
}
