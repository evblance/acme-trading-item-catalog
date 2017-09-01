
(function(jQuery) {

  'use strict';

  function showItemAdminPanel() {
    $(this).find('.admin-panel--item')
    .addClass('admin-panel--item--shown');
  }

  function hideItemAdminPanel() {
    $('.admin-panel--item').removeClass('admin-panel--item--shown');
  }

  function showCategoryAdminPanel() {
    $('.admin-panel--category').removeClass('admin-panel--category--shown');
    $(this).find('.admin-panel--category')
    .toggleClass('admin-panel--category--shown');
  }

  function hideCategoryAdminPanel() {
    $('.admin-panel--category').removeClass('admin-panel--category--shown');
  }

  function toggleCategoryImage() {
    $(this).find('.list__item--categories__img')
    .toggleClass('list__item--categories__img--active');
  }

  var $main = $('.main');

  $main.on('mouseenter', '.list__item--items', showItemAdminPanel);
  $main.on('mouseleave', '.admin-panel--item', hideItemAdminPanel);

  $main.on('mouseenter', '.list__item--categories', showCategoryAdminPanel);
  $main.on('mouseleave', '.list__item--categories', hideCategoryAdminPanel);

  $main.on('mouseenter', '.list__item--categories', toggleCategoryImage);
  $main.on('mouseleave', '.list__item--categories', toggleCategoryImage);

})($);
