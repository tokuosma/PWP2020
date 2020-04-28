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
                showResource(control.href, "Recipes");
            });
        }
        if(controls[RELATIONS.FOOD_ITEMS]){
            let control = controls[RELATIONS.FOOD_ITEMS];
            let navItem = $.parseHTML($('template#nav-item-template').html());
            navbar.append(navItem);
            $(navItem).find('button')
            .text(control.title)
            .click((click) => {
                showResource(control.href, "Food Items");
            });
        }
    });
});

function showResource(href, title){
    let mainContainer = $('div#mainContainer');
    let title_h = mainContainer.find('h1.title');
    let controls_div = mainContainer.find('div.controls');
    let data_div =  mainContainer.find('div.controls');
    let items_div = mainContainer.find('div.items');

    clearMainContainer();

    if(title){
        title_h.text(title);
    }

    $.get(href, function(r){
        renderData(r, data_div);
        let controls = r['@controls'];
        renderControls(r, controls, controls_div);
        let items = r.items;
        renderItems(items, items_div);
    });
}

function renderControls(r, controls, target){

    let control_self = controls['self'];

    for(let key in controls){
        let name = key;
        let control = controls[key];
        let button = $.parseHTML(`<button class="btn mx-2 btn-primary">${name}</button>`);

        switch(control.method){
            case "POST":
                $(button).click(() => {
                    showForm(control.href, control.method, control.schema, null, control_self.href, name);
                });
                break;
            case "PUT":
                $(button).click(() => {
                    showForm(control.href, control.method, control.schema, r, control_self.href, "EDIT: " + control_self.href);
                });
                break;

            case "DELETE":
                break;

            default:
                $(button).click(() => { 
                    showResource(control.href, control.href); 
                });
                break;
        }
        $(target).append(button);
    }
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

function showForm(url, method, schema, data, returnUrl, title){
    
    clearMainContainer();

    let mainContainer = $('div#mainContainer');
    let controls_div = mainContainer.find('div.controls');
    let data_div =  mainContainer.find('div.controls');
    let title_h = mainContainer.find('h1.title');
    title_h.text(title);
    
    let form = $.parseHTML(`<form action="${url} method=${method}"></form>`);

    for(let fieldName in schema.properties){
        let field = schema.properties[fieldName];
        let label = fieldName;
        let required = (schema.required.indexOf(fieldName) >= 0);
        if(required){
            label += "*";
        }
        if(field.type === 'boolean'){
            // Add checkbox
            let inputGroup = $.parseHTML($('template#form-input-boolean-template').html());
            $(inputGroup).find('label').append(label);
            let input = $(inputGroup).find('input');
            input.attr('name', fieldName);
            if(required){
                input.attr('required', true);
            }
            if(data && fieldName in data){
                let value = data[fieldName];
                input.prop('checked', value);
            }
            $(form).append(inputGroup);

        } else if( field.enum ){
            // Add select for enum
            let inputGroup = $.parseHTML($('template#form-input-select-template').html());
            $(inputGroup).find('label').text(label);

            let select = $(inputGroup).find('select');
            select.attr('name', fieldName);
            if(required){
                select.attr('required', true);
            }
            for(let key in field.enum){
                $(select).append(`<option>${field.enum[key]}</option>`);
            }
            if(data && fieldName in data){
                let value = data[fieldName];
                select.val(value);
            }
            $(form).append(inputGroup);

        } else{
            // Add normal input
            let inputGroup = $.parseHTML($('template#form-input-text-template').html());
            $(inputGroup).find('label').text(label);
            let input = $(inputGroup).find('input');
            input.attr('name', fieldName);
            if(required){
                input.attr('required', true);
            }
            if(data && fieldName in data){
                let value = data[fieldName];
                input.val(value);
            }
            $(form).append(inputGroup);
        }
    }

    $(form).append(`<button type="button" class="cancel btn btn-default mx-3">Back</button><button class="btn btn-primary mx-3">Save</button>`);
    $(data_div).append(form);


    $(form).submit( function(event){
        event.preventDefault();
        $.ajax({
            url: url,
            method: method,
            contentType : "application/json",
            data: JSON.stringify(getFormData($(form))),
            success: () =>{
                showResource(returnUrl, returnUrl);
            },
            error: handleAjaxError
        });
    });

    $(form).find('button.cancel').click(function(event){
        showResource(returnUrl, returnUrl);
    });

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

function getFormData($form){
    // from: https://stackoverflow.com/a/11339012/7229327
    var unindexed_array = $form.serializeArray({
        // jQuery extension, see extensions.js
        checkboxesAsBools: true
    });
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
    });

    return indexed_array;
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
        if(!name || name === "undefined"){
            name = url;
        }
        $.get(url, function(r){
            showResource(url, name);
        });
    });
}

function handleAjaxError(jqXHR, textStatus, errorThrown){
    if(jqXHR.responseJSON){
        let message = jqXHR.responseJSON['@error']['@message'];
        toastr.error(message, textStatus);
    }
    else{
        toastr.error(errorThrown,textStatus);
    }
}