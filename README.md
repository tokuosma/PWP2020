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
venv >pytest --cov-report term-missing --cov=climatecook
```
## Usage
1) Set the FLASK_APP environment variable:

```
venv >set FLASK_APP=climatecook
```

Optionally, enable the debugger by setting up the development environment:
```
venv >set FLASK_ENV=development
```

2) Initialize the database with the following command:

```
venv >flask init-db
```

3) Start the API:
```
venv >flask run
venv
 * Serving Flask app "climatecook" (lazy loading)
 * Environment: development
 * Debug mode: on
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 325-295-960
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

The API should now be up and running and the resources should be accessible. The API entry point is http://<host>:<port>/api/ 

The API contains the following resources:

| Resource | url | Description | Methods |
|:-------------------: |:------------:|:--------------------:|:---------------:|
| API Entry | /api/ | API entry point with links to the main collections | GET |
| RecipeCollection | /api/recipes | Collection of all available recipes. New recipes can be added to the collection. | GET, POST |
| Recipe | /api/recipes/{recipe_id} | Represents a single recipe that can be viewed, updated or deleted. New ingredients can be added with post. Also lists all ingredients of the recipe as separate items.| GET, POST, PUT, DELETE |
| Ingredient | /api/recipes/{recipe_id}/ingredients/{ingredient_id} | Represents a single ingredient that can be viewed, updated or deleted| GET, PUT, DELETE |
| FoodItemCollection | /api/food-items | A collection of all available food items. New food items can be added to the collection| GET, POST |
| FoodItem | /api/food-items/{food_item_id} | Represents a single food item that can be viewed, edited or deleted. All the equivalents related to the food item are also returned as separate items and new equivalents can be added with POST | GET, POST, PUT, DELETE |
| FoodItemEquivalent | api/food-items/{food_item_id}/equivalents/{food_item_equivalent_id} | Represents a single food item equivalent that can be viewed, edited or deleted.| GET, PUT, DELETE |
