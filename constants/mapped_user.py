mapped_data = {
    "jarick": "Jarick Montojo",
    "francis": "Francis Calderia",
    "maxi": "Maximo Ignacio",
}

def mapped_user_to_display(name: str) -> str:
    if not mapped_data.get(name):
        print(f"The username '{name}' is not yet added on the mapped_data")
    
    return mapped_data.get(name, "Missing")
    