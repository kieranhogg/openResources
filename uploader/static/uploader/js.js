$(function() {
    $('select[name=syllabus]')
                .empty().append($('<option>---------</option>'))
    $('select[name=unit]')
                .empty().append($('<option></option>'))
    $('select[name=unit_topic]')
                .empty().append($('<option></option>'))
                
});
// FIXME move this and functionise
// get syllabuses for subject
$(document).ready(function(){
    $('select[name=id_subject]').change(function(){
            subject_id = $(this).val();
            $.getJSON("/lookup/syllabus/" + subject_id, null, function(data) {
            $.each(data, function(key, value) {   
             $('select[name=id_syllabus]')
                .append($('<option>', { value : key })
                .text(value)); 
            });
        });
    });
});

// get units for syllabus
$(document).ready(function(){
    $('select[name=syllabus]').change(function(){
            syllabus_id = $(this).val();
            $.getJSON("/lookup/unit/" + syllabus_id, null, function(data) {
            $('select[name=id_unit]')
                .empty().append($('<option></option>'))
            $.each(data, function(key, value) {   
             $('select[name=id_unit]')
                .append($('<option>', { value : key })
                .text(value)); 
            });
        });
    });
});

// get unit topics for unit
$(document).ready(function(){
    $('select[name=id_unit]').change(function(){
            unit_id = $(this).val();
            $.getJSON("/lookup/unit_topic/" + unit_id, null, function(data) {
            $('select[name=id_unit_topic]')
                .empty().append($('<option><option>'))
            $.each(data, function(key, value) {   
             $('select[name=id_unit_topic]')
                .append($('<option>', { value : key })
                .text(value)); 
            });
        });
    });
});

// we set subject on the previous page, fill this in and pre-fill syllabuses
$(document).ready(function(){
    var subject = '{{subject}}';
    $('[name=subject]').val(subject);
    subject_id = $('[name=id_subject]').val();
    $.getJSON("/lookup/syllabus/" + subject_id, null, function(data) {
    $.each(data, function(key, value) {   
     $('select[name=syllabus]')
        .append($('<option>', { value : key })
        .text(value)); 
        });
    });
});