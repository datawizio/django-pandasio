# django-pandasio

## Installation

```bash
pip install git+https://github.com/datawizio/django-pandasio.git
```

## Examples

### DataFrame Serializer
```python
import pandas as pd
import pandasio

from models import Product, Category


class ProductSerializer(pandasio.DataFrameSerializer):

    product_id = pandasio.CharField(max_length=100, source='identififer')
    name = pandasio.CharField(max_length=200)
    category_id = pandasio.IntegerField(required=False, allow_null=True)

    def validate_category_id(self, column):
        # isinstance(column, pd.Series) is True
        if column.isnull().any():
            root_category_id = Category.get_root_category_id()
            column = column.apply(lambda x: x if not pd.isnull(x) else root_category_id)
        return column

    class Meta:
        # django model used to save dataframe into a database
        model = Product
        validators = [
            pandasio.UniqueTogetherValidator(['product_id'])
        ]


dataframe = pd.DataFrame(
    data=[
        ['234556', 'Coca-Cola'],
        ['456454', 'Pepsi']
    ],
    columns=['product_id', 'name']
)

serializer = ProductSerializer(data=dataframe)
if serializer.is_valid():
    serializer.save()
```

### Get detailed validation errors
```python
import pandas as pd
import pandasio


class TestSerializer(pandasio.DataFrameSerializer):

    id = pandasio.IntegerField()
    name = pandasio.CharField(max_length=9)

    class Meta:
        validators = [pandasio.UniqueTogetherValidator(['id', "name"])]


dataframe = pd.DataFrame(
    data=[
        ['234556', 'Coca-Cola'],
        ['234556', 'Coca-Cola'],
        ['234556', None],
        [None, "0123456789"],
    ],
    columns=['id', 'name']
)

serializer = TestSerializer(data=dataframe)
serializer.is_valid()
print(serializer.errors)
"""
{
    'id': {'This column cannot contain null values'},
    'name': {ErrorDetail(string='Ensure column values have no more than 9 characters', code='max_length'), 'This column cannot contain null values'},
    'non_field_errors': [ErrorDetail(string="Ensure values are not duplicated by ['id', 'name']", code='duplicated')]}
"""
print(serializer.human_errors)
"""
    defaultdict(
        <class 'list'>,
        {
            'id': [{'reason': 'NULL_NOT_ALLOWED', 'indexes': [3]}],
            'name': [
                {'reason': 'NULL_NOT_ALLOWED', 'indexes': [2]},
                {'reason': 'MAX_LENGTH_VALUE', 'indexes': [3], 'limit_value': 9}
            ],
            'non_field_errors': [
                {'reason': 'NON_UNIQUE_TOGETHER', 'indexes': [1], 'unique_together_fields': ['id', 'name']}
            ]
        }
    )
"""
```
