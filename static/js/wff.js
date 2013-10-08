
function loadSpreadsheet( ssid, ssname ) {
    $.get('/spreadsheet', { 'ssid': ssid }, function(data) {
        var html = jQuery("<div>").html(data);
        var boxes = html.find('.wff-box');
        for (var i=0;i<boxes.length;i++) {
            var box = boxes.eq(i);
            // create the metadata header
            var boxmeta = box.find('.wff-box-meta').find('span')
            $("#wff-boxes-spreadsheet-container-" + ssid ).append()
            // append the box to the boxcontainer
            var boxdata = box.find('.wff-box-data')
            $("#wff-boxes-spreadsheet-container-" + ssid ).append(boxdata);
        };
        // everything loaded. Set onclick function
        $("#wff-boxes-spreadsheet-heading-" + ssid + " a").text(ssname);
        $("#wff-boxes-spreadsheet-heading-" + ssid + " a").click(function(){
            viewAllBoxes(ssid, boxes.length);
        });
        // setup footable stuff
        $(".footable").footable();
        $(".datepicker").datepicker({ dateFormat: "yy-mm-dd" });
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





/*
<!-- Calendar config -->
<div class='wff-boxes-calendar-container wff-minimized' id='boxheader1'>
    <p>
    <span><strong><a onclick="viewBox(1)">KARINSBOX</a></strong></span>
    <span>scheduled: N/A</span>
    <span><a href='/boxes?flipped=True&ssid=0AvA5wEfgv_7FdE9XbFV2TjVqTkszZjdPbVJHeUxNOUE&boxname=KARINSBOX'>flipped: N/A</a></span>
    <span><a href="javascript:void(0)" onclick="$('#boxaddcalendar1').toggle('fast')">add_to_calendar</a></span>
    </p>

<!-- BOXADD to Calendar menu -->
<div id='boxaddcalendar1' style='display:none'>
<form action="/boxes">
<input style='display:none' name="add" value="True" />
<input style='display:none' name="ssid" value="0AvA5wEfgv_7FdE9XbFV2TjVqTkszZjdPbVJHeUxNOUE" />
<input style='display:none' name="boxname" value="KARINSBOX" />
<table>
    <tr>
        <td>start:</td>
        <td><input type='text' class="datepicker" name="start" size="12" /></td>
    </tr>
    <tr>
        <td>every:</td>
        <td><input name="freq" value="28" size='3'/>days.</td>
    </tr>
    <tr>
        <td>location:</td>
        <td><input type='text' name="location" size="20"/></td>
    </tr>
    <tr>
        <td>calendar:</td>
        <td><select name='clid'>
        <option value="2c34g36p9mcv7hh5ka9qs1o2m0@group.calendar.google.com">IMP Fly Stocks</option>
        </select></td>
    </tr>
    <tr>
        <td></td>
        <td><input type="submit" value="add to calendar"></td>
    </tr>
</table>
</form>
</div>
</div>
*/

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
