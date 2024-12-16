import spacy, time
from spacy.tokens.token import Token
import networkx as nx
import matplotlib.pyplot as plt

class Graph:
    def __init__(self) -> None:
        self.nodes_amount = 0
        self.edges_amount = 0
        self.nodes: dict[str,dict[str,dict]] = {}

    def n_nodes(self): return self.nodes_amount
    def n_edges(self): return self.edges_amount

    def has_node(self,node): return node in self.nodes
    def has_edge(self,u,v): return v in self.nodes[u]['edges'] if self.has_node(u) else False
    def has_relation(self,u,r,v): return self.has_edge(u,v) and self.get_edge_label(u,v) == r


    def get_edge_label(self,u,v):
        if self.has_edge(u,v): return self.nodes[u]['edges'][v]['label']

    def get_node_type(self,node):
        if self.has_node(node): return self.nodes[node]['type']
    

    def get_edges(self):
        return [(u,v) for u in self.nodes for v in self.nodes[u]['edges']]
    
    def get_edges_by_label(self,label):
        return [(u,v) for u,v in self.get_edges() if self.get_edge_label(u,v) == label]
    
    def get_node_edges(self,node):
        return [(n,v) for n,v in self.get_edges() if n == node]
    
    def get_node_edges_by_label(self,node,label):
        return [(n,v) for n,v in self.get_edges_by_label(label) if n == node]
    
    def get_edges_to_node(self,node):
        return [(u,n) for u,n in self.get_edges() if n == node]
    
    def get_edges_to_node_by_label(self,node,label):
        return [(u,n) for u,n in self.get_edges_by_label(label) if n == node]
    

    def get_nodes_pointed_by_node(self,node):
        return [n for _,n in self.get_node_edges(node)]
    
    def get_nodes_pointed_by_node_by_label(self,node,label):
        return [n for _,n in self.get_node_edges_by_label(node,label)]
    
    def get_nodes_pointed_to_node(self,node):
        return [n for n,_ in self.get_edges_to_node(node)]
    
    def get_nodes_pointed_to_node_by_label(self,node,label):
        return [n for n,_ in self.get_edges_to_node_by_label(node,label)]

    def get_nodes_by_type(self,type):
        return [u for u in self.nodes.keys() if self.nodes[u]['type'] == type]


    def add_node(self,node):
        if not self.has_node(node):
            self.nodes.update({node:{'edges':{},'type':''}})
            self.nodes_amount+=1

    def add_edge(self,node_from,node_to,label=''):
        if self.has_node(node_from) and self.has_node(node_to):

            if self.get_node_type(node_from) == '' or self.get_node_type(node_from) == '':
                if label == 'originar':
                    self.nodes[node_from]['type'] = 'genre'
                    self.nodes[node_to]['type'] = 'genre'
                elif label == 'tocar':
                    self.nodes[node_from]['type'] = 'artist'
                    self.nodes[node_to]['type'] = 'genre'
                elif label == 'escutar':
                    self.nodes[node_from]['type'] = 'person'
                    self.nodes[node_to]['type'] = 'artist'
                elif label == 'seguir':
                    self.nodes[node_from]['type'] = 'person'
                    self.nodes[node_to]['type'] = 'person'

            self.nodes[node_from]['edges'].update({node_to:{'label':label}})
            self.edges_amount+=1

    def remove_node(self,node):
        if self.has_node(node):
            self.nodes.pop(node)
            for n in self.get_nodes_pointed_to_node(node):
                self.nodes[n]['edges'].pop(node)
        return node

    def remove_edge(self,node_from,node_to):
        if self.has_node(node_from):
            if self.has_edge(node_from,node_to):
                self.nodes[node_from]['edges'].pop(node_to)
        return (node_from,node_to)


    def recommend_artists(self,person,enhance=False):
        if self.has_node(person) and self.get_node_type(person) == 'person':
            artists = self.get_nodes_by_type('artist')

            known_artists= self.get_nodes_pointed_by_node_by_label(person,'escutar')
            known_artists_styles = {s for a in known_artists for s in self.get_nodes_pointed_by_node_by_label(a,'tocar')}

            recommendations = []
            for a in artists:
                artist_styles = set(self.get_nodes_pointed_by_node_by_label(a,'tocar'))
                if not a in known_artists and known_artists_styles.intersection(artist_styles):
                    recommendations.append(a)

            if enhance: self.__recommend_artists_enhanced(artists,known_artists,known_artists_styles,recommendations)

            return recommendations
        
    def __recommend_artists_enhanced(self,artists,known_artists,known_artists_styles,r:list):
        related_styles = {rs for s in known_artists_styles for rs in self.get_nodes_pointed_by_node_by_label(s,'originar')}
        related_styles.update({rs for s in known_artists_styles for rs in self.get_nodes_pointed_to_node_by_label(s,'originar')})
        for a in artists:
            artist_styles = set(self.get_nodes_pointed_by_node_by_label(a,'originar'))
            if not a in known_artists and related_styles.intersection(artist_styles):
                r.append(a)

    def recommend_users(self,person):
        if self.has_node(person) and self.get_node_type(person) == 'person':
            users = self.get_nodes_by_type('person')
            
            known_artists= set(self.get_nodes_pointed_by_node_by_label(person,'escutar'))
            followed_users = set(self.get_nodes_pointed_by_node_by_label(person,'seguir'))

            recommendations = []
            for u in users:
                if u != person and not u in followed_users:
                    user_artists = set(self.get_nodes_pointed_by_node_by_label(u,'escutar'))
                    user_follows = set(self.get_nodes_pointed_by_node_by_label(u,'seguir'))
                    if known_artists.intersection(user_artists) or followed_users.intersection(user_follows):
                        recommendations.append(u)

            return recommendations


    def plot_users(self):
        nodes = self.get_nodes_by_type('person')

        blank_graph: nx.Graph = nx.empty_graph(len(nodes))

        edges = self.get_edges_by_label('seguir')

        coords = list(nx.shell_layout(blank_graph).values())
        pos = dict([(nodes[i],coords[i]) for i in range(len(nodes))])

        node_labels = dict([(u,u) for u in nodes])

        nx.draw_networkx_nodes(nodes,pos,node_color='tab:blue')

        nx.draw_networkx_edges(blank_graph.to_directed(),pos,edgelist=edges,edge_color='tab:gray')

        nx.draw_networkx_labels(nodes,pos,labels=node_labels)

        plt.plot([0],[0],'gray',label='seguir')

        plt.legend()
        plt.show()

    def plot_genres(self):
        nodes = self.get_nodes_by_type('genre')

        blank_graph: nx.Graph = nx.empty_graph(len(nodes))

        edges = self.get_edges_by_label('originar')

        coords = list(nx.shell_layout(blank_graph).values())
        pos = dict([(nodes[i],coords[i]) for i in range(len(nodes))])

        node_labels = dict([(u,u) for u in nodes])

        nx.draw_networkx_nodes(nodes,pos,node_color='tab:red')

        nx.draw_networkx_edges(blank_graph.to_directed(),pos,edgelist=edges,edge_color='tab:purple')

        nx.draw_networkx_labels(nodes,pos,labels=node_labels)

        plt.plot([0],[0],'purple',label='originar')

        plt.legend()
        plt.show()

    def plot_artists_genres(self):
        nodes = list(self.get_nodes_by_type('artist')) + list(self.get_nodes_by_type('genre'))
        blank_graph: nx.Graph = nx.empty_graph(len(nodes))

        edges = self.get_edges_by_label('tocar')

        coords = list(nx.shell_layout(blank_graph).values())
        pos = dict([(nodes[i],coords[i]) for i in range(len(nodes))])

        node_labels = dict([(u,u) for u in nodes])

        nx.draw_networkx_nodes(self.get_nodes_by_type('artist'),pos,node_color='tab:green')
        nx.draw_networkx_nodes(self.get_nodes_by_type('genre'),pos,node_color='tab:red')

        nx.draw_networkx_edges(blank_graph.to_directed(),pos,edgelist=edges,edge_color='tab:orange')

        nx.draw_networkx_labels(nodes,pos,labels=node_labels)

        plt.plot([0],[0],'orange',label='tocar')

        plt.legend()
        plt.show()

    def plot_artists_users(self):

        nodes = list(self.get_nodes_by_type('artist')) + list(self.get_nodes_by_type('person'))
        blank_graph: nx.Graph = nx.empty_graph(len(nodes))

        edges = self.get_edges_by_label('escutar')

        coords = list(nx.shell_layout(blank_graph).values())
        pos = dict([(nodes[i],coords[i]) for i in range(len(nodes))])

        node_labels = dict([(u,u) for u in nodes])

        nx.draw_networkx_nodes(self.get_nodes_by_type('artist'),pos,node_color='tab:green')
        nx.draw_networkx_nodes(self.get_nodes_by_type('person'),pos,node_color='tab:blue')

        nx.draw_networkx_edges(blank_graph.to_directed(),pos,edgelist=edges,edge_color='k')

        nx.draw_networkx_labels(nodes,pos,labels=node_labels)

        plt.plot([0],[0],'black',label='escutar')

        plt.legend()
        plt.show()

    def plot(self):
    
        blank_graph: nx.Graph = nx.empty_graph(self.nodes_amount)

        nodes = list(self.nodes.keys())
        
        edges = self.get_edges()

        coords = list(nx.shell_layout(blank_graph).values())
        pos = dict([(nodes[i],coords[i]) for i in range(self.nodes_amount)])

        node_labels = dict([(u,u) for u in self.nodes])

        nx.draw_networkx_nodes(self.get_nodes_by_type('genre'),pos,node_color='tab:red')
        nx.draw_networkx_nodes(self.get_nodes_by_type('artist'),pos,node_color='tab:green')
        nx.draw_networkx_nodes(self.get_nodes_by_type('person'),pos,node_color='tab:blue')

        for u,v in edges:
            color = 'k'
            if self.get_edge_label(u,v) == 'originar':
                color = 'tab:purple'
            elif self.get_edge_label(u,v) == 'tocar':
                color = 'tab:orange'
            elif self.get_edge_label(u,v) == 'seguir':
                color = 'tab:gray'
            nx.draw_networkx_edges(blank_graph.to_directed(),pos,edgelist=[(u,v)],edge_color=color)

        nx.draw_networkx_labels(self.nodes,pos,labels=node_labels)

        plt.plot([0],[0],'purple',label='originar')
        plt.plot([0],[0],'orange',label='tocar')
        plt.plot([0],[0],'black',label='escutar')
        plt.plot([0],[0],'gray',label='seguir')

        plt.legend()
        plt.show()






def get_relations(nlp:spacy.Language,text:str):
    doc = nlp(text)
    relations = []
    
    for sent in doc.sents:
        sub = []
        obj = []
        verb = None
        words: dict[Token,dict[list,str,str]] = {}

        for token in sent:

            if token.head in words.keys() and token.text in words[token.head]['full-name']:continue

            words.update({token:{'full-name':token.text,'dep_':token.dep_, 'pos_':token.pos_}})
            
            if token.pos_ in ('PROPN','NOUN'):
                curr_token = token
                while curr_token.nbor().pos_ in ('PROPN','NOUN'):
                    words[token]['full-name'] += ' '+curr_token.nbor().text
                    curr_token = curr_token.nbor()

        for word in words:

            if words[word]['pos_'] == 'VERB':
                verb = word
                sub.extend([c for c in word.children if c.dep_ == 'nsubj' and c.pos_ == 'PROPN' and not c in sub])
                obj.extend([c for c in word.children if c.dep_ in ('obl','obj','pobj','conj','dep')])
            
            if words[word]['dep_'] in ('conj','appos') and word.head in obj:
                obj.append(word)
            elif not verb and words[word]['dep_'] in ('conj','nsubj','nsubj:pass','ROOT','appos') and words[word]['pos_'] in ('PROPN','NOUN'):
                sub.append(word)

        if sub and obj:
            for s in sub:
                for o in obj:
                    relations.append((words[s]['full-name'], verb.lemma_, words[o]['full-name']))

    return relations

def question(nlp:spacy.Language,graph:Graph):
    print('faça uma pergunta (formato: [sujeito(s)] [verbo/relação] [objeto(s)] [?]):',end=' ')
    text = str(input())
    relations = get_relations(nlp,text)
    for u,r,v in relations:
        if not graph.has_relation(u,r,v):
            return False
    return True




nlp = spacy.load('pt_core_news_lg')

g = Graph()

text = ''
with open('texto.txt', 'r') as file:
    for line in file:
        text += line+'. '

rel=get_relations(nlp,text)

for u,_,_ in rel:
    g.add_node(u)
for _,_,v in rel:
    g.add_node(v)
for u,r,v in rel:
    g.add_edge(u,v,r)



print('1 - plotar grafo inteiro')
print('2 - plotar artistas e estilos')
print('3 - plotar artistas e usuários')
print('4 - plotar estilos')
print('5 - plotar usuários')
print('6 - fechar')
print('ra - recomendar artista')
print('ru - recomendar usuário')
print('? - faça uma pergunta (relações)')
print('info - informação sobre nó')


while True:

    cmd = str(input())
    if cmd == '?':
        print(question(nlp,g))
    if cmd == '1':
        g.plot()
    if cmd == '2':
        g.plot_artists_genres()
    if cmd == '3':
        g.plot_artists_users()
    if cmd == '4':
        g.plot_genres()
    if cmd == '5':
        g.plot_users()
    if cmd == '6':
        break
    if cmd == 'ra':
        print('nome:',end=' ')
        person = str(input())
        print('aprimorar (digite qualquer coisa para ativar):',end=' ')
        enhance = bool(input())
        print(g.recommend_artists(person,enhance=enhance))
    if cmd == 'ru':
        print('nome:',end=' ')
        person = str(input())
        print(g.recommend_users(person))
    if cmd == 'info':
        node = str(input())
        if g.has_node(node):
            print('type:',g.nodes[node]['type'])
            print('edges:',g.nodes[node]['edges'])
        else:
            print('nó não encontrado')
    
    time.sleep(1)