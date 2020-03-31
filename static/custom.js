var time = 10;

function ResetTime() {
    time = 10;
}

function refreshData() {
    $('#CountDown').html(time);
    time--;
    PartialRefresh = setTimeout(refreshData, 1000);
}

var FullRefresh = setTimeout(() => {
    LoadSetting('v-pills-Results');
}, 10000);

var PartialRefresh = setTimeout(refreshData, 1000);

function SetFullRefresh() {
    clearTimeout(PartialRefresh);
    FullRefresh = setTimeout(() => {
        LoadSetting('v-pills-Results');
    }, 10000);
}

$(document).ready(function () {
    LoadSetting($('#InitialRoute').val());
})

function LoadSetting(content) {
    var $home = $(document.getElementById(content));
    $('#v-pills-tabContent').children('div').addClass('d-none');
    $home.removeClass('d-none');
    $home.html('Loading...').hide().fadeIn('slow');
    clearTimeout(FullRefresh);
    $('#navbarTogglerDemo01').collapse('toggle')
    $.get($home.data("url"), function (data) {
        $home.html(data).hide().fadeIn('slow');
    });
}

function SetStyle(style, card) {
    $('#TemplateStyle').val(style);
    $('#CardItems').find(".card").removeClass('CardSelect');
    $(card).addClass('CardSelect');
}

function ShowModal() {
    $('#exampleModalCenter').modal('show');
}

function SetSource(Name, Source) {
    $('#imgImagePreview').attr("src", Source);
    $('#imgSave').attr('href', Source);
    $('#imgTitle').html(Name);
}