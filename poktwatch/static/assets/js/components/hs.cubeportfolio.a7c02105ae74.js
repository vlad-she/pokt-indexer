;
(function($) {
    'use strict';
    $.HSCore.components.HSCubeportfolio = {
        _baseConfig: {},
        pageCollection: $(),
        init: function(selector, config) {
            this.collection = selector && $(selector).length ? $(selector) : $();
            if (!$(selector).length) return;
            this.config = config && $.isPlainObject(config) ? $.extend({}, this._baseConfig, config) : this._baseConfig;
            this.config.itemSelector = selector;
            this.initCubeportfolio();
            return this.pageCollection;
        },
        initCubeportfolio: function() {
            var $self = this,
                config = $self.config,
                collection = $self.pageCollection;
            this.collection.each(function(i, el) {
                var $this = $(el),
                    setControls = $this.data('controls'),
                    setLayout = $this.data('layout'),
                    setXGap = $this.data('x-gap'),
                    setYGap = $this.data('y-gap'),
                    setAnimation = $this.data('animation'),
                    setCaptionAnimation = $this.data('caption-animation'),
                    setLoadMoreSelector = $(this).data('load-more-selector'),
                    setLoadMoreAction = $(this).data('load-more-action'),
                    setLoadItemsAmount = $(this).data('load-items-amount'),
                    setDefaultMediaQueries = [{
                        width: 1500,
                        cols: 3
                    }, {
                        width: 1100,
                        cols: 3
                    }, {
                        width: 800,
                        cols: 3
                    }, {
                        width: 480,
                        cols: 2,
                        options: {
                            caption: '',
                            gapHorizontal: 10,
                            gapVertical: 10
                        }
                    }],
                    setMeidaQueries = JSON.parse(el.getAttribute('data-media-queries'));
                $this.cubeportfolio({
                    filters: setControls,
                    layoutMode: setLayout,
                    defaultFilter: '*',
                    sortToPreventGaps: true,
                    gapHorizontal: setXGap,
                    gapVertical: setYGap,
                    animationType: setAnimation,
                    gridAdjustment: 'responsive',
                    mediaQueries: setMeidaQueries ? setMeidaQueries : setDefaultMediaQueries,
                    caption: setCaptionAnimation ? setCaptionAnimation : 'overlayBottomAlong',
                    displayType: 'sequentially',
                    displayTypeSpeed: 100,
                    lightboxDelegate: '.cbp-lightbox',
                    lightboxGallery: true,
                    lightboxTitleSrc: 'data-title',
                    lightboxCounter: '<div class="cbp-popup-lightbox-counter">{{current}} of {{total}}</div>',
                    appendItems: '<div class="logo cbp-item">my awesome content to append to plugin</div> <div class="logo cbp-item">my second awesome content to append to plugin</div>',
                    singlePageInlineDelegate: '.cbp-singlePageInline',
                    singlePageInlinePosition: 'below',
                    singlePageInlineInFocus: true,
                    singlePageInlineCallback: function(url, element) {
                        var t = this;
                        $.ajax({
                            url: url,
                            type: 'GET',
                            dataType: 'html',
                            timeout: 30000
                        }).done(function(result) {
                            t.updateSinglePageInline(result);
                        }).fail(function() {
                            t.updateSinglePageInline('AJAX Error! Please refresh the page!');
                        });
                    },
                    singlePageDelegate: '.cbp-singlePage',
                    singlePageDeeplinking: true,
                    singlePageStickyNavigation: true,
                    singlePageCounter: '<div class="cbp-popup-singlePage-counter">{{current}} of {{total}}</div>',
                    singlePageCallback: function(url, element) {
                        var t = this;
                        $.ajax({
                            url: url,
                            type: 'GET',
                            dataType: 'html',
                            timeout: 10000
                        }).done(function(result) {
                            t.updateSinglePage(result);
                        }).fail(function() {
                            t.updateSinglePage('AJAX Error! Please refresh the page!');
                        });
                    },
                    plugins: {
                        loadMore: {
                            selector: setLoadMoreSelector,
                            action: setLoadMoreAction,
                            loadItems: setLoadItemsAmount
                        }
                    }
                });
                collection = collection.add($this);
            });
        }
    };
})(jQuery);