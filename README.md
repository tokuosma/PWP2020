# PWP SPRING 2020
# CLIMATECOOK API
# Group information
* Student 1. Janne Eskola (janne.eskola@student.oulu.fi)
* Student 2. Toni Kuosmanen (toni.kuosmanen@student.oulu.fi)

## Installation and running the tests:

1. Install the project requirements (preferrably into a virtual environment):
```
venv >pip install -r requirements.txt
venv >pip install pytest
```
2. Install climatecook:
```
venv >pip install -e .
```
3. Run the tests using pytest:
```
venv >pytest
```
Obs! All the tests utilize a temporary database file. If you want to initialize an empty database withot running the tests use the following command:
```
venv >flask init-db
```

## Usage
| Resource | url | Description | Methods |
|:-------------------: |:------------:|:--------------------:|:---------------:|
|: API Entry : |: /api/ :|: API entry point with links to the main collections :|: GET :|
| RecipeCollection | /api/recipes | Collection of all available recipes. New recipes can be added to the collection. | GET, POST |
| Recipe | /api/recipes/{recipe_id} | Represents a single recipe that can be viewed, updated or deleted. New ingredients can be added with post. Also lists all ingredients of the recipe as separate items.| GET, POST, PUT, DELETE |
| Ingredient | /api/recipes/{recipe_id}/ingredients/{ingredient_id} | Represents a single ingredient that can be viewed, updated or deleted| GET, PUT, DELETE |
| FoodItemCollection | /api/food-items | A collection of all available food items. New food items can be added to the collection| GET, POST |
| FoodItem | /api/food-items/{food_item_id} | Represents a single food item that can be viewed, edited or deleted. All the equivalents related to the food item are also returned as separate items and new equivalents can be added with POST | GET, POST, PUT, DELETE |
| FoodItemEquivalent | api/food-items/{food_item_id}/equivalents/{food_item_equivalent_id} | Represents a single food item equivalent that can be viewed, edited or deleted.| GET, PUT, DELETE |

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__


