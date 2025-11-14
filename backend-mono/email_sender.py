import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()  

def envia_email_simples(destinatario: str) -> bool:
    """
    Envia o TCLE via smtplib (Gmail).
    Requer as variáveis de ambiente:
    - EMAIL_FROM: (o seu email@gmail.com verificado)
    - APP_KEY: (a Senha de App de 16 dígitos do Google)
    Retorna True se enviado com sucesso, False caso contrário.
    """
    
    password = os.getenv("APP_KEY")
    from_email = os.getenv("EMAIL_FROM")

    if not password:
        print("Erro: Variável de ambiente APP_KEY não configurada.")
        return False
    if not from_email:
        print("Erro: Variável de ambiente EMAIL_FROM não configurada.")
        return False

    assunto = ("Termo de Consentimento Livre e Esclarecido (TCLE) - "
               "Pesquisa: Do jogo à realidade: a relação da metacognição no reconhecimento de fake news")
    termo_consentimento = (

        """Olá! Você aceitou participar da pesquisa “Do jogo à realidade: a relação da metacognição no reconhecimento de fake news com uso da gamificação”

        Abaixo segue sua via do TCLE com todos os detalhes da pesquisa. Em caso de dúvidas ou desistência em participar da pesquisa basta entrar em contato com a pesquisadora pelos meios abaixo.

        -------------------------------------------------------------
        TERMO DE CONSENTIMENTO LIVRE E ESCLARECIDO

        Você está sendo convidado(a) para participar de uma pesquisa, intitulada "Do jogo à realidade: A relação da metacognição no reconhecimento de fake news com o uso da gamificação". A pesquisa é realizada pela aluna de graduação em Psicologia na Universidade Federal de São Carlos - UFSCar,  Maria Fernanda de Lemos Salicioni sob a orientação da professora Patrícia Waltz Schelini do departamento de Psicologia. Sua participação é livre e voluntária.

        A pesquisa possui o objetivo de avaliar a efetividade do uso de jogos eletrônicos como intervenção no reconhecimento de notícias falsas (fake news) e verificar a relação da metacognição nesse processo. A sua participação consistirá em responder a algumas perguntas relativas a informações pessoais (idade, gênero, identificação étcnico-racial, nível de escolaridade e estado de nascença) e, em seguida, você responderá a um questionário de alinhamento político e um teste que avalia mudança de estratégias metacognitivas. Após isso, será apresentado um pré-teste de notícias falsas antes da intervenção (os jogos) e após a intervenção outras notícias falsas. A pesquisa no total dura entre xx - xx minutos. No entanto, a qualquer momento da pesquisa, você pode optar pela interrupção das respostas, seja continuando posteriormente ou não. O único momento que é necessário a atenção do indivíduo sem interrupção é durante o teste de estratégias metacognitivas. 

        Esta pesquisa foi submetida ao Comitê de Ética em Pesquisa com Seres Humanos (CEP) da Universidade Federal de São Carlos (CAAE: XXXXXXXXXXXX) e aprovada sob o número XXXXX. O CEP, vinculado à Comissão Nacional de Ética em Pesquisa (CONEP), tem a responsabilidade de garantir e fiscalizar que todas as pesquisas científicas com seres humanos obedeçam às normas éticas do País, e que os participantes de pesquisa tenham todos os seus direitos respeitados. O CEP-UFSCar funciona na Pró-Reitoria de Pesquisa da Universidade Federal de São Carlos, localizado no prédio da reitoria (área sul do campus São Carlos).  Endereço: Rodovia Washington Luís, km 235 - CEP: 13.565-905 - São Carlos-SP. E-mail: cephumanos@ufscar.br. Telefone (16) 3351-9685. Horário de atendimento: das 08:30 às 11:30.

        Você é livre para se recusar a participar ou retirar sua autorização, a qualquer momento, em qualquer fase da pesquisa, e isso não trará nenhum prejuízo na sua relação com as pesquisadoras ou com a instituição, ou seja, você não sofrerá nenhuma penalidade ou terá qualquer prejuízo. Sua desistência pode ser comunicada diretamente às pesquisadoras responsáveis através dos seus respectivos endereços eletrônicos a qualquer momento. Não há nenhum custo para participar desta pesquisa e também não há remuneração ou gratificação por parte de qualquer pessoa envolvida.

        Os testes e questionários a serem utilizados não contêm perguntas invasivas à intimidade dos participantes, não oferecendo risco imediato ao(a) senhor(a), mas alguns itens podem remeter a algum desconforto, evocar sentimentos ou lembranças desagradáveis. Além disso, o tempo de resposta e a exposição à tela podem causar cansaço e/ou desconforto, assim como a postura mantida durante o preenchimento das perguntas. Em caso de algum problema ou necessidade de ajuda, a pesquisadora estará disponível nos meios de contato disponibilizados abaixo, de acordo com a necessidade dos participantes, para qualquer dúvida ou diálogo, visando acolher os desconfortos suscitados.

        Os benefícios que este trabalho poderá trazer não são diretos nem imediatos. Os resultados serão utilizados para dar mais suporte científico às pesquisas que se propõem a aumentar o reconhecimento de fake news no contexto digital e sua relação com a metacognição. Futuramente, esses achados poderão servir para fundamentos para elaborar intervenções mais efetivas nesse desempenho.

        Apesar de não haver garantia total de sigilo das informações da pesquisa por conta de limitações características dos meios eletrônicos, as pesquisadoras empregarão esforços para a preservação do sigilo. Os dados dessa pesquisa serão coletados através de um site criado pelas próprias pesquisadoras, em que somente as pesquisadoras responsáveis terão acesso às respostas.

        As pesquisadoras responsáveis se comprometem a tornar públicos nos meios acadêmicos e científicos os resultados obtidos ao final da pesquisa, sejam eles favoráveis ou não, sem qualquer identificação de indivíduos participantes. Assim que os dados da pesquisa forem publicados, você poderá ter acesso ao resultado na íntegra. As respostas são anônimas e serão armazenadas em local seguro por cinco anos e, depois desse tempo, serão apagadas.

        Considerando estes termos, ao participar, você autoriza a divulgação dos dados coletados referentes à sua participação. O(a) senhor(a) receberá uma via deste termo via email, em que consta o telefone e o endereço do pesquisador principal e responsável com quem você poderá tirar suas dúvidas sobre a pesquisa e sua participação agora ou a qualquer momento. Sugerimos que guarde uma cópia.

        Ao final da pesquisa, a pesquisadora irá enviar por email os resultados obtidos, de maneira
        clara e acessível, a todos os participantes que optarem por recebê-los.

        Ao clicar na opção “Li e estou de acordo com os termos da pesquisa”, você informa que leu todas as informações e declara que concorda em participar da pesquisa nos termos deste TCLE. Caso não concorde em participar, apenas clique na opção “Li e não quero participar da pesquisa” que o direciona a uma página de agradecimento e em seguida feche a página do navegador. As pesquisadoras ficarão à disposição para eventuais esclarecimentos durante e após a sua participação.

        -------------------------------------------------------------\n\n"""
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = assunto
    message["From"] = from_email
    message["To"] = destinatario

    # Criar a parte de texto puro (plain text)
    part1 = MIMEText(termo_consentimento, "plain", "utf-8")
    
    # Criar a parte de HTML (copiando a lógica original de substituir \n por <br/>)
    part2 = MIMEText(termo_consentimento.replace("\n", "<br/>"), "html", "utf-8")
    
    # Anexar as partes à mensagem
    # O cliente de e-mail escolherá qual versão exibir
    message.attach(part1)
    message.attach(part2)

    # 4. Configurar a conexão SMTP para o Gmail
    smtp_server = "smtp.gmail.com"
    port = 465  # Para SSL
    
    # Criar um contexto SSL seguro
    context = ssl.create_default_context()

    print(f"Tentando enviar e-mail para {destinatario} via Gmail SMTP...")

    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(from_email, password)
            print("Login SMTP bem-sucedido.")
            
            server.sendmail(
                from_email, destinatario, message.as_string()
            )
            
            print(f"Email enviado com sucesso para {destinatario}!")
            return True
            
    except smtplib.SMTPException as e:
        print(f"Erro de SMTP ao tentar enviar email para {destinatario}: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao enviar email para {destinatario}: {e}")
        return False