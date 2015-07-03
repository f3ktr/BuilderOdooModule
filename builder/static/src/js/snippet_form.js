(function () {
    function publish(message){
        parent.postMessage(JSON.stringify(message), '*');
    }

    var channels = {
        'snippet.html.set': function (data, event){
            $('#url').val(data.url);
            $('#xpath').val(data.xpath);
            $('#html').val(data.content);
            $('#form-snippet').find('input, textarea').removeClass('error');
        }
    };

    window.addEventListener("message", function (event) {
        var data = JSON.parse(event.data);
        var handler = channels[data.channel];
        if (handler){
            handler(data, event);
        }
    }, false);

    $('#form-snippet-options').submit(function (){
        return false
    }).change(function (){
        var $this = $(this);
        publish({
            channel: 'site.options',
            options: {
                css: {
                    copy: $this.find('#copy-css').is(':checked')

                },
                images: {
                    inline : $this.find('#copy-css').is(':checked')
                },
                position: {
                    vertical : $this.find('input[name="position-vertical"]:checked').val(),
                    horizontal : $this.find('input[name="position-horizontal"]:checked').val()
                }
            }
        });
    });

    $('#form-snippet').submit(function (event){
        var has_errors = false;
        $(this).find('input[type="text"], textarea').each(function (){
            var $this = $(this);
            var has_value = $this.val();
            if (!has_value){
                has_errors = true;
            }
            $this.toggleClass('error', !has_value);
        });
        if (has_errors){
            event.preventDefault();
            event.stopPropagation();
        }

        return !has_errors;
    }).find('input, textarea').change(function (){
        var $this = $(this);
        $this.toggleClass('error', !$this.val());
    });



})();