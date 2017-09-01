/*
 * CATALOG.js - Main scripts for Web UI
 */


(function(jQuery) {

  'use strict';

  // Animates item admin panel options into view
  function showItemAdminPanel() {
    $(this).find('.admin-panel--item')
    .addClass('admin-panel--item--shown');
  }

  // Animates item admin panel options out of view
  function hideItemAdminPanel() {
    $('.admin-panel--item').removeClass('admin-panel--item--shown');
  }

  // Animates category admin panel options into view
  function showCategoryAdminPanel() {
    $('.admin-panel--category').removeClass('admin-panel--category--shown');
    $(this).find('.admin-panel--category')
    .toggleClass('admin-panel--category--shown');
  }

  // Animates category admin panel options out of view
  function hideCategoryAdminPanel() {
    $('.admin-panel--category').removeClass('admin-panel--category--shown');
  }

  // Toggles category images from view
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
