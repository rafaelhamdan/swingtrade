# swingtrade
## Setting up development environment
This application requires a Python 3 interpreter.

To build the application, start a virtual environment using `venv`:

<details><summary>On Linux</summary>
<p>

```python
python3 -m venv env
source ./env/bin/activate
python install -r requirements.txt
```

</p>
</details>
<details><summary>On Windows</summary>
<p>

```python
Python -m venv env
.\env\Scripts\activate.bat
Pip install -r requirements.txt
```

</p>
</details>

Pip will install all the required packages, and you should be able to start the application:
```
python main.py
```
