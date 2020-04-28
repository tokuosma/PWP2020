/* jshint -W097 */
"use strict";

const API_URL = "/api/";

const RELATIONS = {
    RECIPES : "clicook:recipes-all",
    FOOD_ITEMS: "clicook:food-items-all"
};

$(document).ready(function(e){
    $.get(API_URL, function(r){
        let navbar = $('#navbarNav ul.navbar-nav');
        navbar.empty();
        let controls = r['@controls'];  
        if(controls[RELATIONS.RECIPES]){
            let control = controls[RELATIONS.RECIPES];
            let navItem = $.parseHTML($('template#nav-item-template').html());
            navbar.append(navItem);
            $(navItem).find('button')
            .text(control.title)
            .click((click) => {
                showCollection(control.href, "Recipes");
            });
        }
        if(controls[RELATIONS.FOOD_ITEMS]){
            let control = controls[RELATIONS.FOOD_ITEMS];
            let navItem = $.parseHTML($('template#nav-item-template').html());
            navbar.append(navItem);
            $(navItem).find('button')
            .text(control.title)
            .click((click) => {
                showCollection(control.href, "Food Items");
            });
        }
    });
});

function showCollection(href, title){
    let mainContainer = $('div#mainContainer');
    let title_h = mainContainer.find('h1.title');
    let controls = mainContainer.find('div.controls');
    let data_div =  mainContainer.find('div.controls')
    let items_div = mainContainer.find('div.items');

    clearMainContainer();

    if(title){
        title_h.text(title);
    }

    $.get(href, function(r){
        renderData(r, data_div);
        let items = r.items;
        renderItems(items, items_div);
    });
}

function renderData(r, target){
    let fields = []
    for( let field in r ){
        if(field.startsWith('@')){
            // skip Mason fields
            continue;
        } else if(field === 'items'){
            // skip items
            continue;
        }
        else{
            fields.push({label:field, value: r[field]});
        }
    }

    let row = $.parseHTML('<div class="row"></div>');
    for(let i = 0; i < fields.length; i++){
        if(i % 4 === 0){
            $(target).append(row);
            row = $.parseHTML('<div class="row"></div>');
        }
        $(row).append($.parseHTML(`<div class="col-lg-3"><label>${fields[i].label}</label><p>${fields[i].value}</p></div>`));
    }
    $(target).append(row);
}

function renderItems(items, target){
    if(!items){
        return;
    } else if((items.length) === 0){
        target.append('<h2>The collection is empty.</h2>');
    } else{
        let item = items[0];
        let controls = item['@controls'];
        let columns = [];
        for (var property in item){
            if(property.startsWith('@')){
                // Skip Mason properties.
                continue;
            }
            columns.push({
                "data" : property,
                "title": property
            });
        }
        
        if(controls){
            columns.push({
                "data": "@controls",
                "title": "Actions",
                "orderable": false,
                "searchable": false,
                "render": renderControlsDT
            });
        }

        let table = $.parseHTML('<table style="width: 100%;" class="table table-hover table-bordered"></table>');
        target.append(table);
        $(table).DataTable({
            data: items,
            columns: columns,
            drawCallback: function(settings){
                initControlsDT(table);
            }
        });
    }
}

function clearMainContainer(){
    let mainContainer = $('div#mainContainer');
    mainContainer.find('h1.title').empty();
    mainContainer.find('div.controls').empty();
    mainContainer.find('div.data').empty();
    mainContainer.find('div.items').empty();
    // Clear any existing Datatables
    let tables = $.fn.dataTable.tables();
    for(var i = 0; i < tables.length; i++){
        let dt = $(tables[i]).DataTable();
        dt.destroy();
    }

}

function renderControlsDT(data, type, row, meta){

    let markup = "";

    if(data.self){
        markup += '<button class="btn btn-primary show-item" data-url="' + data.self.href +
        '" data-name="' + row.name + '" >Show</button>';
    }
    return markup;
}

function initControlsDT(table){
    $(table).find('button.show-item').off('click').click( function(event){
        let url = $(event.currentTarget).data('url');
        let name = $(event.currentTarget).data('name');
        if(!name | name === "undefined"){
            name = url;
        }
        $.get(url, function(r){
            showCollection(url, name);
        });
    });
}