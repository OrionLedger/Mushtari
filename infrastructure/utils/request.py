import requests

def make_get_request(url, headers=None, params=None):
    """Make a GET request to the specified URL."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"GET request failed: {e}")
    
    
def make_post_request(url, headers=None, data=None):
    """Make a POST request to the specified URL."""
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"POST request failed: {e}")
    

def make_put_request(url, headers=None, data=None):
    """Make a PUT request to the specified URL."""
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"PUT request failed: {e}")
    

def make_delete_request(url, headers=None):
    """Make a DELETE request to the specified URL."""
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.status_code == 204
    except requests.RequestException as e:
        print(f"DELETE request failed: {e}")
