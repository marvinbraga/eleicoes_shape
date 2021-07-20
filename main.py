# coding=utf-8
"""
Example Module
"""
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

import settings


class EleicaoPorMunicipio:
    """ Classe de eleição por município. """

    def __init__(self, shape_file, data_file):
        self._shape_file = os.path.join(settings.BASE_PATH, os.path.normpath(shape_file))
        self._data_file = os.path.join(settings.BASE_PATH, os.path.normpath(data_file))
        self._data = None
        self._shape = None
        self._dt_votacao = None

    def load(self):
        """ load data """
        self._shape = gpd.read_file(self._shape_file)
        self._data = pd.read_csv(self._data_file, sep=';', encoding='latin1')
        return self

    @property
    def shape(self):
        """ Returns shape """
        return self._shape

    @property
    def data(self):
        """ Returns data """
        return self._data

    @property
    def dt_votacao(self):
        """ Returns temp data """
        return self._dt_votacao

    def show_map(self, data):
        """ Exibe mapa """
        _, ax = plt.subplots(figsize=(12, 12))
        cma = ListedColormap(['red', 'green'])
        ax = data.plot(column='RESULTADO', cmap=cma, legend=False, linewidth=0.1, ax=ax, edgecolor='grey')
        ax.set_axis_off()
        ax.set_title(
            'Resultado Eleição 2018 / Município / 2 Turno',
            fontdict={'fontsize': '25', 'fontweight': '3'})
        ax.annotate(
            'Fonte: IBGE, 2014; TSE, 2019; Jornal Estado de SP, 2019',
            xy=(0.1, 0.08), xycoords='figure fraction', horizontalalignment='left',
            verticalalignment='top', fontsize=10, color='#555555'
        )
        red_patch = mpatches.Patch(color='red', label='Os bandidos')
        green_patch = mpatches.Patch(color='green', label='Bolsomito')
        ax.legend(handles=[red_patch, green_patch])
        plt.show()
        return self

    def normalize_data(self):
        """ Ajusta os dados. """
        # Recupera os dados apenas do 2 turno
        self._data = self._data[self._data['NR_TURNO'] == 2]
        # Retira as cidades inválidas
        df_vot = self._data[self._data['SG_UF'] != 'ZZ']
        # Recupera apenas as colunas que serão utilizadas
        df_vot = df_vot[
            ['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS']]
        # Agrupa os dados para recupera as soma por município
        df_vot = df_vot.groupby(
            ['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO']).sum().reset_index()
        # Reordena os dados
        df_vot.sort_values(by=['SG_UF', 'NM_MUNICIPIO', 'QT_VOTOS_NOMINAIS'], ascending=False, inplace=True)
        # Deixa apenas a informação do candidato vencedor
        df_vot = df_vot.drop_duplicates(subset=['SG_UF', 'NM_MUNICIPIO'], keep='first')
        # Cria coluna para facilitar leitura do resultado
        df_vot['RESULTADO'] = df_vot['NR_CANDIDATO'].apply(lambda x: int(x) == 17)
        self._dt_votacao = df_vot
        return self


def main():
    """ Main process """
    dados = ['./shapefile_BR/BR_Municipios_2020.shp', './data/votacao_candidato_munzona_2018_BR.csv']
    eleicao = EleicaoPorMunicipio(*dados).load().normalize_data()
    # Recupera o dataframe com a correspondência de códigos entre TSE e IBGE
    df_equivalencia = pd.read_csv('./data/correspondencia-tse-ibge.csv', sep=';', encoding='latin1')
    # Recupera dados
    df_mapa = eleicao.shape.copy()
    df_voto_novo = eleicao.dt_votacao.copy()
    df_equiv_novo = df_equivalencia.copy()
    # Coloca o index com o mesmo código do município
    df_voto_novo.set_index('CD_MUNICIPIO', drop=False, inplace=True)
    df_equiv_novo.set_index('COD_TSE', drop=False, inplace=True)

    if len(df_equiv_novo) == len(df_voto_novo):
        # Faz o merge dos dataframes em um novo
        df_vot_equiv = df_voto_novo.join(df_equiv_novo)
        # Faz ajustes para fazer novo merge com o dataframe do mapa
        df_vot_equiv['GEOCOD_IBGE'] = df_vot_equiv['GEOCOD_IBGE'].astype(str)
        df_mapa.set_index('CD_MUN', drop=False, inplace=True)
        df_vot_equiv.set_index('GEOCOD_IBGE', drop=False, inplace=True)
        # Faz merge
        df_mapa_novo = df_mapa.join(df_vot_equiv)
        # Apaga dados inválidos
        df_mapa_novo.drop(columns='AJUSTE', inplace=True)
        df_mapa_novo.dropna(inplace=True)
        # Exibe o mapa
        eleicao.show_map(df_mapa_novo)


if __name__ == '__main__':
    main()
