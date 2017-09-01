/*
 * STOCK.js - Custom plugin for generating stock levels
 *            via colored bars
 */

var BARWIDTH = 50;
var BARHEIGHT = 24;

var stockScale = d3.scaleLinear()
                   .domain([0, 100])
                   .range([0, BARWIDTH]);

var colorScale = d3.scaleLinear()
                   .domain([0, 10, 20, 9999])
                   .range(['red', 'orange', 'lightgreen', 'green']);

// TODO: Add tooltips to bars
// var tooltip = d3.select('.stock-bar')
//                  .append('div')
//                  .style('position', 'absolute')
//                  .style('padding', '0 10px')
//                  .style('background', '#ddd')
//                  .style('opacity', '0.5');

function insertStockbar(id, stock) {
    var selectString = '#' + id + ' .item__stock';

    d3.select(selectString)
      .append('svg')
      .classed('stock-bar', 'true')
      .attr('width', BARWIDTH)
      .attr('height', BARHEIGHT)
      .style('background', '#fff')
      .append('rect')
      .attr('width', 0)
      .attr('height', BARHEIGHT)
      .attr('fill', colorScale(stock))

      .transition()
        .delay(100)
        .duration(1000)
        .ease(d3.easeCubic)
        .attr('width', stockScale(stock));
}


$(document).ready(function() {

  var $items = $('.item');
  var numItems = $items.length;
  var id, item, stock;

  for (var i = 0; i < numItems; i++) {
    item = $items[i];
    id = $(item).attr('id');
    stock = $items[i].dataset.stock;
    insertStockbar(id, stock);
  }

});
