print("Conectando ao MongoDB...")
# conectando ao MongoDB
from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://example:user:examplehash@mongodbteste.1nwmch7.mongodb.net/?appName=mongoDbTeste"
)

db = client["trabalho_bd"]
leads = db["leads"]
usuarios = db["usuarios"]
# conectando ao MongoDB - fim

# CRUD Usuarios
def insert_usuario(usuario_data):
    result = usuarios.insert_one(usuario_data)
    return result.inserted_id

def read_usuario(email_data):
    return usuarios.find_one({"email": email_data})

def read_all_usuarios():
    for usuario in usuarios.find():
        print(usuario)

def update_usuario(email_data, update_data):
    result = usuarios.update_one(
        {"email": email_data},
        {"$set": update_data}
    )
    return result.modified_count

def delete_usuario(email_data):
    result = usuarios.delete_one({"email": email_data})
    return result.deleted_count

# CRUD Usuarios - fim

# CRUD Leads
def insert_lead(lead_data):
    result = leads.insert_one(lead_data)
    return result.inserted_id

def read_lead(email_data):
    lead = leads.find_one({"email": email_data})
    return lead

def read_all_leads():
    for lead in leads.find():
        print(lead)

def delete_lead(email_data):
    result = leads.delete_one({"email": email_data})
    return result.deleted_count
     
# CRUD Leads - fim

# CRUD Empresas
def insert_company(company_data):
    result = db["companies"].insert_one(company_data)
    return result.inserted_id

def read_company(cnpj_data):
    company = db["companies"].find_one({"cnpj": cnpj_data})
    return company

def read_all_companies():
    for company in db["companies"].find():
        print(company)

def update_company(cnpj_data, update_data):
    result = db["companies"].update_one(
        {"cnpj": cnpj_data},
        {"$set": update_data}
    )
    return result.modified_count

def delete_company(cnpj_data):
    result = db["companies"].delete_one({"cnpj": cnpj_data})
    return result.deleted_count
# CRUD Empresas - fim

# CRUD Pesquisas

searches = db["searches"]

def create_search(search_data, lead_list):
    search_data["leads"] = lead_list
    result = searches.insert_one(search_data)
    return result.inserted_id

def read_search(search_id):
    return searches.find_one({"_id": search_id})

def add_lead_to_search(search_id, lead_data):
    searches.update_one(
        {"_id": search_id},
        {"$push": {"leads": lead_data}}
    )

def delete_search(search_id):
    result = searches.delete_one({"_id": search_id})
    return result.deleted_count

# CRUD Pesquisas - fim


print("Começando os testes com MongoDB...")


# recriando leads para a pesquisa
lead1 = {
    "nome": "Empresa Z",
    "email": "vendas@empresa.com",
    "cnpj": "33.333.333/0001-33"
}

lead2 = {
    "nome": "Empresa W",
    "email": "comercial@empresa.com",
    "cnpj": "44.444.444/0001-44"
}

l1 = insert_lead(lead1)
l2 = insert_lead(lead2)

search = {
    "termo_busca": "empresas de tecnologia",
    "usuario": "joao@email.com",
    "data_pesquisa": "2026-02-02"
}

search_id = create_search(
    search,
    [
        {"lead_id": l1, "ordem": 1, "relevancia": 0.95},
        {"lead_id": l2, "ordem": 2, "relevancia": 0.82}
    ]
)

print("Pesquisa criada:", search_id)

print("Pesquisa no banco:")
print(read_search(search_id))


delete_search(search_id)
print("Pesquisa deletada.")

