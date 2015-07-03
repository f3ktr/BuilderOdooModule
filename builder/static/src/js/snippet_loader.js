if (window.jQuery) {
    window.jQuery.noConflict();
}

(function () {

    function script(url, callback) {
        var new_script = document.createElement('script');
        new_script.src = url + '?__stamp=' + Math.random();
        new_script.type = 'text/javascript';
        new_script.onload = new_script.onreadystatechange = callback;
        document.getElementsByTagName('head')[0].appendChild(new_script);
    }


    window.getBase64Image = function getBase64Image(img) {
        var canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        return canvas.toDataURL("image/png");
    };

    var odoo;

    function publish(message) {
        odoo.get()[0].contentWindow.postMessage(JSON.stringify(message), '*');
    }

    script(window.odooUrl + '/builder/static/lib/jquery.js', function () {
        var path = [];
        var index = false;
        var preservePath = false;

        script(window.odooUrl + '/builder/static/lib/jquery.js');
        script(window.odooUrl + '/web/static/lib/jquery.hotkeys/jquery.hotkeys.js', function (){
            $(document).bind('keydown', 'ctrl+up', function (){
                console.log(index, path.length);
                var $active = $('.bookmarklet-active');
                if ($active){
                    preservePath = true;
                    path = [$active.parent().click()].concat(path);
                    preservePath = false;
                    index = 0;
                }
                return false;
            });
            $(document).bind('keydown', 'ctrl+down', function (){
                console.log(index, path.length);
                var $current = path[index];
                if (index < path.length - 1){
                    index++;
                    $current = path[index];
                }
                if ($current){
                    preservePath = true;
                    $current.click();
                    preservePath = false;
                }
                return false;
            });
            $(document).bind('keydown', 'ctrl+left', function (){
                var $current = path[index];
                if ($current){
                    $current = $current.prev();
                    path[index] = $current;
                    path = path.slice(0, index+1);
                    preservePath = true;
                    $current.click();
                    preservePath = false;
                }
                return false;
            });
            $(document).bind('keydown', 'ctrl+right', function (){
                var $current = path[index];
                if ($current){
                    $current = $current.next();
                    path[index] = $current;
                    path = path.slice(0, index+1);
                    preservePath = true;
                    $current.click();
                    preservePath = false;
                }
                return false;
            });

        });
        script(window.odooUrl + '/builder/static/lib/jquery.getStyleObject.js');
        function loadCss(url) {
            $('<link />').attr({
                "rel": "stylesheet",
                "type": "text/css",
                "href": url + '?__stamp=' + Math.random()
            }).appendTo('head');
        }

        function iframe(url, callback) {
            var iframe = $('#odooIframe');
            if (!iframe.length) {
                iframe = $('<iframe/>').attr('id', 'odooIframe').appendTo('body').addClass('top right');
            }
            iframe.on('load', callback);
            iframe.attr('src', url);
            return iframe;
        }

        odoo = iframe(window.newSnippetUrl);
        var options = {
            css: {
                copy: true
            },
            images: {
                inline: true
            },
            position: {
                vertical: 'top',
                horizontal: 'right'
            }
        };

        var channels = {
            'site.options': function (data, event) {
                options = $.extend(options, data.options);
                $(odoo).removeClass('top down left right').addClass(options.position.vertical + ' ' + options.position.horizontal)
            }
        };


        window.addEventListener("message", function (event) {
            var data = JSON.parse(event.data);
            var handler = channels[data.channel];
            if (handler) {
                handler(data, event);
            }
        }, false);

        /* Create iframe */
        loadCss(window.odooUrl + '/builder/static/src/css/bookmarklet.css');


        function css(element) {
            var css_rules = {};
            var rules = window.getMatchedCSSRules(element.get(0));
            for (var rule in rules) {
                if (rules.hasOwnProperty(rule)) {
                    css_rules = $.extend(css_rules, css2json(rules[rule].style), css2json(element.attr('style')));
                }
            }
            return css_rules;
        }

        function css2json(css) {
            var s = {};
            if (!css) return s;
            if (css instanceof CSSStyleDeclaration) {
                for (var i in css) {
                    if (css.hasOwnProperty(i)) {
                        if ((css[i]).toLowerCase) {
                            s[(css[i]).toLowerCase()] = (css[css[i]]);
                        }
                    }
                }
            }
            else if (typeof css == "string") {
                css = css.split("; ");
                for (i in css) {
                    if (css.hasOwnProperty(i)) {
                        var l = css[i].split(": ");
                        s[l[0].toLowerCase()] = (l[1]);
                    }
                }
            }
            return s;
        }

        function applyCssInline($elem) {
            if (options.css.copy) {
                $elem.css(css($elem));
            }
        }


        function getXPath(node) {
            var comp, comps = [];
            var xpath = '';
            var getPos = function (node) {
                var position = 1, curNode;
                if (node.nodeType == Node.ATTRIBUTE_NODE) {
                    return null;
                }
                for (curNode = node.previousSibling; curNode; curNode = curNode.previousSibling) {
                    if (curNode.nodeName == node.nodeName) {
                        ++position;
                    }
                }
                return position;
            };

            if (node instanceof Document) {
                return '/';
            }

            for (; node && !(node instanceof Document); node = node.nodeType == Node.ATTRIBUTE_NODE ? node.ownerElement : node.parentNode) {
                comp = comps[comps.length] = {};
                switch (node.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + node.nodeName;
                        break;
                    case Node.PROCESSING_INSTRUCTION_NODE:
                        comp.name = 'processing-instruction()';
                        break;
                    case Node.COMMENT_NODE:
                        comp.name = 'comment()';
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = node.nodeName;
                        break;
                }
                comp.position = getPos(node);
            }

            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name;
                if (comp.position != null) {
                    xpath += '[' + comp.position + ']';
                }
            }

            return xpath;

        }


        $(document).on('click', '*', function processElement(event) {
            event.stopPropagation();
            event.preventDefault();

            var $fixed = $(this);
            $('.bookmarklet-active').removeClass('bookmarklet-active');

            applyCssInline($fixed);
            $fixed.find('*').each(function () {
                applyCssInline($(this));
            });

            if (options.images.inline) {
                if ($fixed.is('img:not(.processed)')) {
                    $fixed.attr('src', getBase64Image($fixed[0])).addClass('processed');
                }

                $fixed.find('img:not(.processed)').each(function () {
                    var $this = $(this);
                    $this.attr('src', getBase64Image(this)).addClass('processed');
                });
            }

            $fixed.addClass('bookmarklet-active');
            if (!preservePath){
                path = [$fixed];
                index = 0;
            }

            publish({
                channel: 'snippet.html.set',
                xpath: getXPath(this),
                content: this.outerHTML,
                url: window.location.href
            });

            return false;

        });
    });


})();