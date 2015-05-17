$(function() {
    $('select[name=syllabus]')
                .empty().append($('<option>---------</option>'))
    $('select[name=unit]')
                .empty().append($('<option></option>'))
    $('select[name=unit_topic]')
                .empty().append($('<option></option>'))
                
    $('select[name=subject]').change(function(){
            subject_id = $(this).val();
            $.getJSON("/lookup/syllabus/" + subject_id, null, function(data) {
            $.each(data, function(key, value) {   
             $('select[name=syllabus]')
                .append($('<option>', { value : key })
                .text(value)); 
            });
        });
    });


// get units for syllabus
    $('select[name=syllabus]').change(function(){
            syllabus_id = $(this).val();
            $.getJSON("/lookup/unit/" + syllabus_id, null, function(data) {
            $('select[name=id_unit]')
                .empty().append($('<option></option>'))
            $.each(data, function(key, value) {   
             $('select[name=unit]')
                .append($('<option>', { value : key })
                .text(value)); 
            });
        });
    });


// get unit topics for unit

    $('select[name=unit]').change(function(){
            unit_id = $(this).val();
            $.getJSON("/lookup/unit_topic/" + unit_id, null, function(data) {
            // $('select[name=unit_topic]')
            //     .empty().append($('<option><option>'))
            
            var self = this;
            this.section = false;
            count = 0;
            $.each(data, function(key, value) {
                if (value.section) {
                    if (!self.section || value.section != self.section) {
                        if (count != 0) {
                            $('select[name=unit_topic]').append('</optgroup>');
                        }
                        count++;
                        $('select[name=unit_topic]').append('<optgroup label=" &gt; ' + value.section + '">');
                        self.section = value.section;
                    }
                }
                 $('select[name=unit_topic]')
                    .append($('<option>', { value : value.id })
                    .text(value.unit_topic)); 
                });
        });
    });


// we set subject on the previous page, fill this in and pre-fill syllabuses
    var subject = '{{subject}}';
    if (subject != "") {
        $('[name=subject]').val(subject);
        subject_id = $('[name=id_subject]').val();
        $.getJSON("/lookup/syllabus/" + subject_id, null, function(data) {
        $.each(data, function(key, value) {   
         $('select[name=syllabus]')
            .append($('<option>', { value : key })
            .text(value)); 
            });
        });
    }
});