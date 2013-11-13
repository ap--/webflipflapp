/* WebFlipFlapp
 *
 *  javascript things
 *
 */

// ~~~ BOXES ~~~ //
//
function wffBoxesLoaded( ssid ) {
    /* this function gets called in boxdata.html
     * and adds its content to boxes.html
     */
    var myframe = $('#wff-boxes-workaround-' + ssid).contents();
    // this lives in boxdata.html
    var header = myframe.find('.breadcrumb');
    var boxes = myframe.find('.thumbnails');
    // theese ids live in boxes.html
    $('#wff-boxes-spreadsheet-heading-' + ssid + " ul" ).replaceWith(header);
    $('#wff-boxes-spreadsheet-container-' + ssid).append(boxes);
    $('#wff-boxes-workaround-' + ssid).remove();
}

function wffBoxesError( ssid, errormsg ) {
    $('#wff-boxes-spreadsheet-heading-' + ssid + " i" )
        .removeClass('icon-spinner icon-spin').addClass('icon-warning-sign');
    $('#wff-boxes-spreadsheet-container-' + ssid).html(
        '<div class="alert alert-error">' + errormsg + '</div>'
    );
}


// ~~~ FLIES ~~~
//
function wffFliesLoaded( ssid ) {
    /* this function gets called in flydata.html
     * and adds its content to flies.html
     */
    // this lives in flydata.html
    var flies = $('#wff-flies-workaround-' + ssid).contents().find('tbody');
    // theese live in flies.html
    $('#wff-boxes-flies-'+ssid).replaceWith(flies);
    $('.table').trigger('footable_redraw');
    $('#wff-box-loader-'+ssid).removeClass('label-warning').addClass('label-success');
    $('#wff-box-loader-'+ssid+' i').removeClass('icon-spinner icon-spin').addClass('icon-ok');
    $('#wff-flies-workaround-' + ssid).remove();
}

function wffFliesError( ssid, errormsg ) {
    $('#wff-box-loader-'+ssid).removeClass('label-warning').addClass('label-important');
    $('#wff-box-loader-'+ssid+' i')
        .removeClass('icon-spinner icon-spin').addClass('icon-warning-sign');
    var error = $('<div class="alert alert-error">' + errormsg + '</div>');
    $('#wff-box-error').append(error);
}


function wffFliesSetup() {
    // eneables filtering on footable in flies.html
    $('table').footable().bind('footable_filtering', 
        function (e) {
            var selected = $('.filter-status').find(':selected').text();
            if (selected && selected.length > 0) {
                e.filter += (e.filter && e.filter.length > 0) ? ' ' + selected : selected;
                e.clear = !e.filter;
            };
        });
    $('.filter-status').change(function (e) {
            e.preventDefault();
            $('table').trigger('footable_filter', {filter: $('#filter').val()});
        });
}

function wffFliesGetFilteredData() {
    // gets called in flies.html when clicked on Download Labels
    var flies = [];
    var data = $("tbody tr")
                .filter(function() { return $(this).css("display") == "table-row" });
    for (var i=0; i<data.length;i++) {
        var row = data.eq(i).find('td');
        var fly = {};
        fly['Label'] = row.eq(0).text();
        fly['Short Identifier'] = row.eq(1).text();
        fly['Genotype'] = row.eq(2).text();
        flies.push(fly);
    }
    $('#wff-flies-form-data').val(JSON.stringify(flies));
    return true;
}

function wffImpossibleError( ssid ) {
    $('#wff-box-loader-'+ssid).removeClass('label-warning').addClass('label-important');
    $('#wff-box-loader-'+ssid+' i')
        .removeClass('icon-spinner icon-spin').addClass('icon-bolt');
    alert('Oh my God! Run!');
}



