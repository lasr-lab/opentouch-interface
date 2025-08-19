This document contains a list of all Streamlit widgets the OpenTouch Interface supports for payload.
Each widget's parameters are mandatory. The key `default` is the value of the widget when it first renders.
It is equivalent to what the Streamlit documentation usually refers to as the `value`, `index` or `default`.

#### [Slider](https://docs.streamlit.io/develop/api-reference/widgets/st.slider)
```yaml
type: slider                    # Widget type, always 'slider'.
label: Select Age               # Description displayed to the user, must be unique.
min_value: 0                    # Minimum value (float). Default: 0.
max_value: 100                  # Maximum value (float). Default: 10.
step: 1                         # Step size (float). Default: 1.
default: 25                     # Initial slider value (float). Default: min_value.
```

#### [Text Input](https://docs.streamlit.io/develop/api-reference/widgets/st.text_input)
```yaml
type: text_input                # Widget type, always 'text_input'.
label: Enter Your Name          # Description displayed to the user, must be unique.
default: "John Doe"             # Initial text input value (str). Default: "".
```

#### [Checkbox](https://docs.streamlit.io/develop/api-reference/widgets/st.checkbox)
```yaml
type: checkbox                      # Widget type, always 'checkbox'.
label: Accept Terms and Conditions  # Description displayed to the user, must be unique.
default: false                      # Initial checkbox state (bool). Default: False.
```

#### [Multiselect](https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect)
```yaml
type: multiselect                             # Widget type, always 'multiselect'.
label: Choose Your Hobbies                    # Description displayed to the user, must be unique.
options: ['Reading', 'Traveling', 'Cooking']  # List of available options (list of str). Default: [].
default: ['Reading', 'Cooking']               # Default selected values; subset of options (list of str). Default: empty list
```

#### [Radio](https://docs.streamlit.io/develop/api-reference/widgets/st.radio)
```yaml
type: radio                           # Widget type, always 'radio'.
label: Select Your Gender             # Description displayed to the user, must be unique.
options: ['Male', 'Female', 'Other']  # List of available options (list of str). Default: [].
default: 'Male'                       # Default value (str). Defaults to the first element in options.
```

#### [Selectbox](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox)
```yaml
type: selectbox                   # Widget type, always 'selectbox'.
label: Choose Your Country        # Description displayed to the user, must be unique.
options: ['USA', 'Canada', 'UK']  # List of available options (list of str). Default: [].
default: 'USA'                    # Default value (str). Defaults to the first element in options or None if options are empty.
```

#### [Number Input](https://docs.streamlit.io/develop/api-reference/widgets/st.number_input)
```yaml
type: number_input              # Widget type, always 'number_input'.
label: Enter Your Height (cm)   # Description displayed to the user, must be unique.
min_value: 50                   # Minimum value (float). Default: 0.
max_value: 250                  # Maximum value (float). Default: 100.
step: 1                         # Step size (float). Default: 1.
default: 170                    # Default value (float). Defaults to min_value.
```