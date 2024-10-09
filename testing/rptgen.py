import json
import re

def groom_code_str(code):
    # Replace \n with <br>
    formatted_str = code.replace('\n', '<br>')

    # Replace sequences of spaces with &nbsp;
    #formatted_str = formatted_str.replace(' ', '&nbsp;')
    return formatted_str 

def groom_narrative(text):
    variable_pattern = re.compile(r'\?[\w]+')
    groomed_narrative = variable_pattern.sub(lambda x: f'<span class="vars">{x.group(0)}</span>', text)
    return groomed_narrative
    

def get_category_class(category):
    """
    Returns the CSS class based on the category value.
    """
    if category == 'X':
        return 'category-X'
    elif category in [1,2]:
        return 'category-1'  # or 'category-2' since they share the same background color
    else:
        return 'category-other'

    
def main():
    """
If target cat <= computed cat, we are green.
If computed cat > target cat AND < 5, we are yellow.
If computed cat > 5, we are red
If computed cat is X, we are red

Light Blue: #e6f7ff
Light Yellow: 

    """
    
    print("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    .category-ok {
        background-color: #e6ffe6;  /* Very light green */
    }
    .category-iffy {
    /*background-color: #fff9e6  light yellow */
        background-color: #fff176
    }    
    .category-X {
        background-color: #ffe6e6;  /* Light red */
    }
    .category-other {
        background-color: #f2f2f2;  /* Default light gray */
    }
    </style>

    <style>
    <style>
    /* General table styling */
    table {
        width: 100%;
        border-collapse: collapse;
    }

    /* Styling for the top row of each major section */
    tr.major-row {
        margin-bottom: 20px;  /* Create a gap between the major rows */
    }

    /* Adjust border to emphasize separation */
    tr.major-row td {
        border-top: 4px solid black;  /* Thicker border at the top of major rows */
        padding: 8px;  /* Padding for better spacing */
    }

    /* Styling for the narrative row */
    tr.spanned-row td {
        border-top: 0;  /* Remove border between major row and narrative */
        padding-bottom: 20px;  /* Increase bottom padding for space before next major row */
    }

    /* Apply some padding inside narrative cells */
    .narrative {
/*        font-style: italic;*/
        padding: 10px 0;
    }
</style>

    </style>
    
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #f2f2f2;
        }
        .query {
            width: 20%;
        }

       .vars {
         font-family: "Courier New", Courier, monospace;  /* Fixed-width font */
         font-weight: bold;  /* Bold text */
         background-color: #f2f2f2;  /* Light gray background */
        }

        .response, .ami-response {
            width: 35%;
            font-family: "Courier New", Courier, monospace;
            font-size: 0.8em; /* Smaller font for response columns */
        }
        .spanned-row td {
            border-top: 0; /* Remove top border of spanned narrative row */
        }
    </style>
    <title>Table Example</title>
</head>
<body>
    """)

        
    # Start table PLUS header row:
    print("""
    <table>
        <tr>
        <th>Name</th>
        <th>#</th>
        <th class="query">Query</th>
        <th class="response">Target Response</th>
        <th class="ami-response">AMI Response</th>
        <th>Cat<br>Max/Calc</th>
    </tr>""")
    
    with open("z.json","r") as fd:
        for line in fd:
            doc = json.loads(line)

            cat_str = ""

            if doc['status'] == 'FAIL':
                category = 'X'
                category_class = 'category-X'                
            else:
                category_class = 'category-other'
                        
                if doc['target_response'] == 'cannot_answer':
                    doc['ami_response'] = '&lt;CANNOT_ANSWER&gt;'
                else:
                    comp_category = doc['computed_cat']
                    targ_category = doc['target_cat']                

                    if str(comp_category) == 'X':
                        category_class = 'category-X'
                    elif comp_category <= targ_category:
                        category_class = 'category-ok'
                    elif (comp_category > targ_category) and comp_category < 5:
                        category_class = 'category-iffy'
                    elif comp_category >= 5:
                        category_class = 'category-X'
                    else:
                        category_class = 'category-other'                    

                    cat_str = str(targ_category) + '/' + str(comp_category)


            if doc['ask'] > 1:
                name_str = ""
            else:
                name_str = doc['name']

            qq = """        
    <tr class="major-row %s">
        <td rowspan="2">%s</td>
        <td rowspan="2">%d</td>
        <td class="query">%s</td>
        <td class="response">%s</td>
        <td class="ami-response">%s</td>
        <td>%s</td> <!-- "Cat" column only appears in this row -->
    </tr>
    
    <tr class="spanned-row">
        <td colspan="5" class="narrative">%s</td>
    </tr>
    """ % (category_class,
           name_str, doc['ask'],
           doc['query'],
               groom_code_str(doc['target_response']),groom_code_str(doc['ami_response']),
           cat_str,
               groom_narrative(doc['msg']))

            print(qq)
            
           #print(doc)
    print("</table>")

    
    print("""</BODY></HTML>""")            
            
if __name__ == "__main__":
    main()
    
