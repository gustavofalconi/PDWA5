from flask import Flask, jsonify, request, session
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'chave_secreta'

conexao = mysql.connector.connect(
    host='bancopdw.mysql.database.azure.com',
    user='projetopwd',
    password='Gustavo123',
    database='projetopdw',
)

if conexao.is_connected():
    
#USERS#

    @app.route('/users/signup', methods=['POST'])
    def criar_usuario():
        criarUsuario= request.get_json()

        if 'nome' in criarUsuario and 'email' in criarUsuario and 'senha' in criarUsuario and 'status' in criarUsuario and 'tipo' in criarUsuario:
            nome    = criarUsuario.get('nome')
            senha   = criarUsuario.get('senha')
            email   = criarUsuario.get('email')
            status  = criarUsuario.get('status')
            tipo    = criarUsuario.get('tipo')
            
            tipos_validos = ['comprador', 'vendedor', 'administrador']
            status_validos = ['ativo', 'inativo']
            
            if tipo not in tipos_validos or status not in status_validos:
                response = {
                    'ERRO': 'Tipo ou status inválidos: Opções tipo: comprador, vendedor e administrador  -  Opções status: ativo e inativo'
                }
                return jsonify(response)

            cursor = conexao.cursor()
            
            cursor = conexao.cursor()
            
            # Verificar se o e-mail já existe no banco de dados
            verificarEmailSQL = f'SELECT COUNT(*) FROM usuario WHERE email = "{email}"'
            cursor.execute(verificarEmailSQL)
            resultadoVerificacao = cursor.fetchone()[0]

            if resultadoVerificacao > 0:
                cursor.close()
                response = {
                'ERRO': 'E-mail já registrado. Escolha outro e-mail.'
                }
                return jsonify(response)

            # Gere um hash da senha usando bcrypt
            senhaCripto = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
            senhaCripto = senhaCripto.decode('utf-8')

            criarUsuarioSQL = f'INSERT INTO usuario (nome, email, senha, status, tipo) VALUES ("{nome}", "{email}", "{senhaCripto}", "{status}", "{tipo}")'
            
            cursor.execute(criarUsuarioSQL)

            conexao.commit()
            cursor.close()

            response = {
                'usuario'   : nome,
                'email'     : email,
                'senha'     : senhaCripto,
                'status'    : status,
                'tipo'      : tipo 
            }
            return jsonify(response)
        
        else:
            response = {
                'ERRO': 'Dados Inválidos'
            }
            return jsonify(response)

    @app.route('/users/login', methods=['POST'])
    def login_usuario():
        login = request.get_json()
        
        email = login.get('email')
        senha = login.get('senha')
        
        cursor = conexao.cursor()

        # Verifique se o e-mail existe no banco de dados
        verificarEmail = f'SELECT usuario_id, email, senha FROM usuario WHERE email = "{email}"'
    
        cursor.execute(verificarEmail)
    
        resultadoEmail = cursor.fetchone()
    
        cursor.close()
        

        if resultadoEmail:
            # Se o e-mail existir, continue com a verificação de senha
            senhaCripto = resultadoEmail[2].encode('utf-8')
            

            if bcrypt.checkpw(senha.encode('utf-8'), senhaCripto):
                session['email'] = email

                response = {
                    'id': resultadoEmail[0],
                    'email': resultadoEmail[1],
                    'mensagem': 'Login feito com sucesso!'
                }
                return jsonify(response)
            else:
                response = {
                    'ERRO': 'Senha Inválida!'
                }
                return jsonify(response)
        else:
            response = {
                'ERRO': 'E-mail não encontrado!'
            }
            return jsonify(response)

    @app.route('/users/logout', methods=['POST'])
    def logout_usuario():
        if 'email' in session:
            email = session.pop('email', None)

            response = {
                'mensagem'   : 'Sessão finalizada com sucesso'
            }
            
            return jsonify(response)
        
        else:
            response = {
                'ERRO': 'Sem usuário logado'
            }
            return jsonify(response)

    @app.route('/users/<int:id>', methods=['PUT'])
    def editar_usuario(id):
        if 'email' not in session:
            response = {
                'ERRO': 'Não está logado'
            }
            return jsonify(response)
        
        editarUsuario = request.get_json()
        
        nome    = editarUsuario.get('nome')
        senha   = editarUsuario.get('senha')
        email   = editarUsuario.get('email')
        status  = editarUsuario.get('status')
        tipo    = editarUsuario.get('tipo')
        
        cursor = conexao.cursor()
        
        # Hash da senha com bcrypt
        senhaCripto = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        
        editarUsuario = f'UPDATE usuario SET nome = "{nome}", email = "{email}", senha = "{senhaCripto}", status = "{status}", tipo = "{tipo}" WHERE usuario_id = "{id}"'
        
        cursor.execute(editarUsuario)

        conexao.commit()
        cursor.close()

        response = {
            'usuario'   : nome,
            'email'     : email,
            'senha'     : senhaCripto.decode('utf-8'),
            'status'    : status,
            'tipo'      : tipo 
        }
        return jsonify(response)

    @app.route('/users/<int:id>', methods=['DELETE'])
    def excluir_usuario(id):
        if 'email' not in session:
            response = {
                'ERRO': 'Realize o login primeiro!'
            }
            return jsonify(response)
    
        cursor = conexao.cursor()

        softDeleteUsuario = f'UPDATE usuario SET status = "inativo" WHERE usuario_id = "{id}"'
        cursor.execute(softDeleteUsuario)

        conexao.commit()
        cursor.close()

        response = {
            'mensagem': 'Usuário marcado como inativo'
        }
        return jsonify(response)
    
#Administradores#

    @app.route('/admin/login', methods=['POST'])
    def login_admin():
        
        login = request.get_json()
        
        email = login.get('email')
        senha = login.get('senha')
        
        cursor = conexao.cursor()

        # Verifique se o e-mail existe no banco de dados
        verificarEmail = f'SELECT usuario_id, email, senha, tipo FROM usuario WHERE email = "{email}"'
    
        cursor.execute(verificarEmail)
    
        resultadoEmail = cursor.fetchone()
    
        cursor.close()
        

        if resultadoEmail:
            # Se o e-mail existir, continue com a verificação de senha
            if resultadoEmail[3] == 'administrador':
                senhaCripto = resultadoEmail[2].encode('utf-8')
                

                if bcrypt.checkpw(senha.encode('utf-8'), senhaCripto):
                    session['email'] = email

                    response = {
                        'id': resultadoEmail[0],
                        'email': resultadoEmail[1],
                        'mensagem': 'Login feito com sucesso!'
                    }
                    return jsonify(response)
                else:
                    response = {
                        'ERRO': 'Senha Inválida!'
                    }
                    return jsonify(response)
            else:
                response = {
                    'ERRO': 'Usuário não é um administrador!'
                }
                return jsonify(response)
        else:
            response = {
                'ERRO': 'E-mail não encontrado!'
            }
            return jsonify(response)


    @app.route('/admin/logout', methods=['POST'])
    def logout_admin():
        
        if 'email' in session:
            email = session.pop('email', None)

            response = {
                'admin'     : email,
                'message'   : 'Administrador acabou de sair da sessão!'
            }
            return jsonify(response)
        
        else:
            response = {
                'message': 'Nenhum Administrador logado!'
            }
            return jsonify(response)


    @app.route('/admin/users', methods=['GET'])
    def mostrar_usuario():
        
        if 'email' not in session:
            response = {
                'message': 'Nenhuma conta conectada'
            }
            return jsonify(response)
        
        cursor = conexao.cursor()
        
        listaUsuarios = "SELECT * FROM usuario"    
        
        cursor.execute(listaUsuarios)
        
        usuarios = cursor.fetchall()
        cursor.close()

        usuariosJson = [
            {
                'id'        : usuario[0], 
                'nome'      : usuario[1], 
                'email'     : usuario[2], 
                'senha'     : usuario[3], 
                'status'    : usuario[4], 
                'tipo'      : usuario[5]
            } 
            for usuario in usuarios
        ]
        return jsonify(usuariosJson)

#Categoria#
    @app.route('/categories', methods=['POST'])
    def criar_categoria():
        
        categoria = request.get_json()
        
        if 'nome' in categoria and 'descricao' in categoria:
        
            nome        = categoria.get('nome')
            descricao   = categoria.get('descricao')
            
            cursor = conexao.cursor()

            criaCategoria = f'INSERT INTO categoria (nome, descricao) VALUES ("{nome}", "{descricao}")' 
            cursor.execute(criaCategoria)

            conexao.commit()
            cursor.close()

            response = {
                'categoria'      : nome,
                'descricao'   : descricao
            }
            return jsonify(response)
        
        else:
            response = {
                'error': 'Dados inválidos'
            }
            return jsonify(response)



    @app.route('/categories/<int:id>', methods=['PUT'])
    def editar_categoria(id):
        
        categoria = request.get_json()
        
        if 'nome' in categoria and 'descricao' in categoria:
        
            nome        = categoria.get('nome')
            descricao   = categoria.get('descricao')
        
            cursor = conexao.cursor()

            editaCategoria = f'UPDATE categoria SET nome = "{nome}", descricao = "{descricao}" WHERE categoria_id = "{id}"' 
            cursor.execute(editaCategoria)

            conexao.commit()
            cursor.close()

            response = {
                'category'      : nome,
                'description'   : descricao
            }
        
        else:
            response = {
                'error': 'Dados inválidos'
            }
        return jsonify(response)


    @app.route('/categories', methods=['GET'])
    def mostrar_categoria():
        
        cursor = conexao.cursor()
        
        listaCategoria = "SELECT * FROM categoria"       
        cursor.execute(listaCategoria)
        
        categorias = cursor.fetchall()
        cursor.close()

        categoriasJson = [
            {
                'id'            : categoria[0], 
                'categoria'      : categoria[1], 
                'descricao'   : categoria[2]
            } 
            
            for categoria in categorias
        ]
        return jsonify(categoriasJson)


    @app.route('/categories/<int:id>', methods=['DELETE'])
    def excluir_categoria(id):
    
        cursor = conexao.cursor()

        excluiCategoria = f'DELETE FROM categoria WHERE categoria_id = "{id}"'  
        
        cursor.execute(excluiCategoria)  

        conexao.commit()
        cursor.close()

        response = {
            'message': 'Categoria excluída'
        }
        return jsonify(response)

#Item#
    @app.route('/items/login', methods=['POST'])
    def login_vendedor():
        
        login = request.get_json()
        
        email = login.get('email')
        senha = login.get('senha')
        
        cursor = conexao.cursor()

        # Verifique se o e-mail existe no banco de dados
        verificarEmail = f'SELECT usuario_id, email, senha, tipo FROM usuario WHERE email = "{email}"'
    
        cursor.execute(verificarEmail)
    
        resultadoEmail = cursor.fetchone()
    
        cursor.close()


        if resultadoEmail:
            # Se o e-mail existir, continue com a verificação de senha
            if resultadoEmail[3] == 'vendedor':
                senhaCripto = resultadoEmail[2].encode('utf-8')
                

                if bcrypt.checkpw(senha.encode('utf-8'), senhaCripto):
                    session['email'] = email

                    response = {
                        'id': resultadoEmail[0],
                        'email': resultadoEmail[1],
                        'mensagem': 'Login feito com sucesso!'
                    }
                    return jsonify(response)
                else:
                    response = {
                        'ERRO': 'Senha Inválida!'
                    }
                    return jsonify(response)
            else:
                response = {
                    'ERRO': 'Usuário não é um vendedor'
                }
                return jsonify(response)
        else:
            response = {
                'ERRO': 'E-mail não encontrado!'
            }
            return jsonify(response)


    @app.route('/items/logout', methods=['POST'])
    def logout_usuario_vendedor():
        
        if 'email' in session:
        
            email = session.pop('email', None)

            response = {
                'usuario'      : email,
                'message'   : 'Vendedor deslogado'
            }
            return jsonify(response)
        
        else:
            response = {
                'message': 'Nenhum vendedor logado'
            }
            return jsonify(response) 


    @app.route('/items', methods=['POST'])
    def criar_itens():
        
        if 'email' not in session:
            response = {
                'message': 'Realize o login'
            }
            return jsonify(response)
        
        item = request.get_json()
        
        if 'titulo' in item and 'autor' in item and 'categoria_id' in item and 'preco' in item and 'descricao' in item and 'status' in item and 'data' in item and 'vendedor_id' in item:
        
            titulo          = item.get('titulo')
            autor           = item.get('autor')
            categoria_id    = item.get('categoria_id')
            preco           = item.get('preco')
            descricao       = item.get('descricao')
            status          = item.get('status')
            data            = item.get('data')
            vendedor_id     = item.get('vendedor_id')
            
            cursor = conexao.cursor()

            criaItem = f'INSERT INTO item (titulo, autor, categoria_id, preco, descricao, status, data, vendedor_id) VALUES ("{titulo}", "{autor}", "{categoria_id}", "{preco}", "{descricao}", "{status}", "{data}", "{vendedor_id}")' 
            cursor.execute(criaItem)

            conexao.commit()
            cursor.close()

            response = {
                'titulo'         : titulo,
                'autor'          : autor,
                'categoria_id'   : categoria_id,
                'preco'          : preco,
                'descricao'      : descricao,
                'status'         : status,
                'data'           : data,
                'vendedor_id'    : vendedor_id
            }
            
            return jsonify(response)
        
        else:
            response = {
                'error': 'Dados inválidos'
            }
            return jsonify(response)


    @app.route('/items', methods=['GET'])
    def mostrar_itens():
        
        if 'email' not in session:
            response = {
                'message': 'Realize o login'
            }
            return jsonify(response)
        
        cursor = conexao.cursor()
        
        selecionaItem = "SELECT * FROM item"       
        cursor.execute(selecionaItem)
        
        items = cursor.fetchall()
        cursor.close()

        item_json = [
            {
                'id'           : item[0], 
                'titulo'       : item[1], 
                'autor'        : item[2], 
                'categoria_id' : item[3], 
                'preco'        : item[4], 
                'descricao'    : item[5],
                'status'       : item[6],
                'data'         : item[7],
                'vendedor_id'  : item[8]
            } 
            for item in items
        ]
        return jsonify(item_json)


    @app.route('/items/<int:id>', methods=['GET'])
    def mostrar_item_especifico(id):
        
        if 'email' not in session:
            response = {
                'message': 'Realize o login'
            }
            return jsonify(response)
        
        cursor = conexao.cursor()
        
        selecionaItem = f'SELECT * FROM item WHERE item_id = "{id}"'       
        cursor.execute(selecionaItem)
        
        items = cursor.fetchall()
        cursor.close()

        item_json = [
            {
                'id'            : item[0], 
                'titulo'         : item[1], 
                'autor'        : item[2], 
                'categoria_id'   : item[3], 
                'preco'         : item[4], 
                'descricao'   : item[5],
                'status'        : item[6],
                'data'          : item[7],
                'vendedor_id'     : item[8]
            } 
            for item in items
        ]
        return jsonify(item_json)


    @app.route('/items/<int:id>', methods=['PUT'])
    def editar_item(id):
        
        if 'email' not in session:
            response = {
                'message': 'Realize o login' 
            }
            return jsonify(response)
        
        item = request.get_json()
        
        titulo          = item.get('titulo')
        autor           = item.get('autor')
        categoria_id    = item.get('categoria_id')
        preco           = item.get('preco')
        descricao       = item.get('descricao')
        status          = item.get('status')
        data            = item.get('data')
        vendedor_id     = item.get('vendedor_id')
        
        cursor = conexao.cursor()

        editaItem = f'UPDATE item SET titulo = "{titulo}", autor = "{autor}", categoria_id = "{categoria_id}", preco = "{preco}", descricao = "{descricao}", status = "{status}", data = "{data}", vendedor_id = "{vendedor_id}" WHERE item_id = "{id}"'
        
        cursor.execute(editaItem)

        conexao.commit()
        cursor.close()

        response = {
                'titulo'         : titulo, 
                'autor'        : autor, 
                'categoria_id'   : categoria_id, 
                'preco'         : categoria_id, 
                'descricao'   : descricao,
                'status'        : status,
                'data'          : data,
                'vendedor_id'     : vendedor_id
            } 
        
        return jsonify(response)


    @app.route('/items/<int:id>', methods=['DELETE'])
    def excluir_item(id):
    
        if 'email' not in session:
            response = {
                'message': 'Realize o login primeiro!'
            }
            return jsonify(response)
    
        cursor = conexao.cursor()

        softDeleteItem = f'UPDATE item SET status = "inativo" WHERE item_id = "{id}"'
        cursor.execute(softDeleteItem)

        conexao.commit()
        cursor.close()

        response = {
            'mensagem': 'Item marcado como inativo'
        }
        return jsonify(response)
    
    @app.route('/items/search', methods=['GET'])
    def buscar_itens():
        
        if 'email' not in session:
            response = {'message': 'Realize o login'}
            return jsonify(response)

        # Obtenha os parâmetros de pesquisa da solicitação
        titulo = request.args.get('titulo', default='', type=str)
        autor = request.args.get('autor', default='', type=str)

        cursor = conexao.cursor(dictionary=True)

        # Construa a consulta SQL com base nos parâmetros de pesquisa
        consultaItem = "SELECT * FROM item WHERE 1=1"
        parametros = {}

        if titulo:
            consultaItem += " AND titulo LIKE %(titulo)s"
            parametros['titulo'] = f"%{titulo}%"

        if autor:
            consultaItem += " AND autor LIKE %(autor)s"
            parametros['autor'] = f"%{autor}%"

        cursor.execute(consultaItem, parametros)

        items = cursor.fetchall()
        cursor.close()

        item_json = [
            {
                'item_id': item['item_id'],
                'titulo': item['titulo'],
                'autor': item['autor'],
                'categoria_id': item['categoria_id'],
                'preco': item['preco'],
                'descricao': item['descricao'],
                'status': item['status'],
                'data': item['data'],
                'vendedor_id': item['vendedor_id']
            }
            for item in items
        ]

        return jsonify(item_json)
    
#Transação#
    @app.route('/transactions', methods=['POST'])
    def criar_transacao():
        
        transacao = request.get_json()
        
        if 'comprador_id' in transacao and 'vendedor_id' in transacao and 'item_id' in transacao and 'data' in transacao and 'preco' in transacao:
        
            comprador_id    = transacao.get('comprador_id')
            vendedor_id     = transacao.get('vendedor_id')
            item_id         = transacao.get('item_id')
            data            = transacao.get('data')
            preco           = transacao.get('preco')
            
            cursor = conexao.cursor()

            criaTransacao = f'INSERT INTO transacao (comprador_id, vendedor_id, item_id, data, preco) VALUES ("{comprador_id}", "{vendedor_id}", "{item_id}", "{data}", "{preco}")' 
            cursor.execute(criaTransacao)

            conexao.commit()
            cursor.close()

            response = {
                'comprador_id'  : comprador_id,
                'vendedor_id' : vendedor_id,
                'item_id'   : item_id,
                'data'      : data,
                'preco'     : preco
            }
            return jsonify(response)
        
        else:
            response = {
                'error': 'Dados inválidos'
            }
            return jsonify(response)


    @app.route('/transactions/<int:user_id>', methods=['GET'])
    def mostrar_transacoes_usuario(user_id):
            cursor = conexao.cursor()

            selecionaTransacoes = f'''
                SELECT t.transacao_id, c.nome AS comprador_nome, v.nome AS vendedor_nome, i.titulo AS nome_item, t.preco, t.data as data_transacao
                FROM transacao t
                JOIN usuario c ON t.comprador_id = c.usuario_id
                JOIN usuario v ON t.vendedor_id = v.usuario_id
                JOIN item i ON t.item_id = i.item_id
                WHERE c.usuario_id = {user_id} OR v.usuario_id = {user_id}
            '''
            
            cursor.execute(selecionaTransacoes)
            transacoes = cursor.fetchall()
            cursor.close()

            transacao_json = [
                {
                    'id': transacao[0],
                    'nome_comprador': transacao[1],
                    'nome_vendedor': transacao[2],
                    'titulo_item': transacao[3],
                    'preco': transacao[4],
                    'data': transacao[5]
                }
                for transacao in transacoes
            ]

            return jsonify(transacao_json)
        
app.run(port=5000, host='localhost', debug=True)        