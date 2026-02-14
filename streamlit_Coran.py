import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import re

import folium
from branca.element import Figure

st.set_page_config(layout="wide")

title1, title2 = st.columns([0.7, 0.3])

with title1 :
  st.title('Coran')
  st.write("Outil de lecture, recherche et statistiques sur le Coran")
  st.write("Source : Données récupérées depuis le site https://www.le-coran.com/ ; image : https://pxhere.com/fr/photo/618662")
  
  st.write("Mise à jour du 13/02/2025 : Première mise en ligne.")
  st.write("Le mode Lecture offre une présentation en texte, confortable pour lire, tandis que le mode Recherche / Analyse présente les données sous forme de tableaux ainsi que des statistiques.")

with title2 :
  st.image('image_Coran.jpg')
  st.write('Julie')

#Chargement du DataFrame étudié :
df = pd.read_excel('Coran_sommaire.xlsx')
df["index"] = df["index"].astype(str)
df["Num_verset"] = df["Num_verset"].astype(str)

#####

st.title('Sourate Al-Fatiha')

fatiha = df[df["index"] == "1"]
fatiha = fatiha[["Num_verset", "Texte"]].set_axis(['Verset n°', 'Texte'], axis = 1)
for _, row in fatiha.iterrows():
    st.write(row["Verset n°"] + " - " + row["Texte"])

page = st.sidebar.radio("Navigation",["🔎 Recherche / Analyse", "📖 Lecture"])

st.title('Recherche de versets')

with st.form("filtres"):

    col_sourate, col_num_sourate, col_num_verset, col_mot = st.columns(4)

    with col_sourate :  
        sourates = [i for i in df["Titre_Français"].unique()]
        sourate = st.multiselect("Sourate :", sourates)

    with col_num_sourate : 
        num_sourate = st.text_input(
        "Numéros de sourates (séparés par des virgules) :", placeholder="")

    with col_num_verset :
        versets = st.text_input(
        "Numéros de versets (séparés par des virgules) :", placeholder="")

    with col_mot :
        mots_cles = st.text_input(
        "Mots(s) recherché(s) (séparés par des virgules) :", placeholder="")
        mode_recherche = st.radio("Mode de recherche :",["OU (au moins un mot)", "ET (tous les mots)"], horizontal=True)

    submit = st.form_submit_button("🔍 Appliquer les filtres")

    select = df.copy()

    if submit:

        if sourate:
            select = select[select["Titre_Français"].isin(sourate)]

        if num_sourate:
            nums = [n.strip() for n in num_sourate.split(",") if n.strip()]
            select = select[select["index"].isin(nums)]

        if versets:
            nums_v = [v.strip() for v in versets.split(",") if v.strip()]
            select = select[select["Num_verset"].isin(nums_v)]

        if mots_cles:
            mots = [m.strip() for m in mots_cles.split(",") if m.strip()]

            if mode_recherche.startswith("OU"):
                # 🔹 Mode OU
                pattern = "|".join(re.escape(m) for m in mots)
                select = select[select["Texte"].str.contains(pattern, case=False, na=False)]

            else:
                # 🔹 Mode ET
                for mot in mots:
                    pattern = re.escape(mot)
                    select = select[select["Texte"].str.contains(pattern, case=False, na=False)]

        st.write(f"Lignes correspondantes : {select.shape[0]}")

        st.title('Résultats')

        if len(select) > 0 :
            select_sourates = select[['index', 'titre_phonétique', 'Titre_Français', 'Titre_Arabe', 'nb_versets']].drop_duplicates()
            select['Sourate'] = select[['index', 'titre_phonétique', 'Titre_Français']].agg(' - '.join, axis=1)
            
            f"Les critères sélectionnés renvoient à {select.shape[0]} verset(s), dans {select_sourates.shape[0]} sourates :"
            
            
            if page == "🔎 Recherche / Analyse":
                
                st.markdown(f"## Sourates :")
                st.data_editor(select_sourates[['index', 'titre_phonétique', 'Titre_Français', 'Titre_Arabe', 'nb_versets']].set_axis(['Sourate n°', 'Titre phonétique', 'Titre Français', 'Titre Arabe', 'Nb de versets'], axis = 1),
                                use_container_width=True)

                if mode_recherche.startswith("ET"):
                    st.markdown(f"## Versets contenant l'ensemble des mots choisis :")
                else :
                    st.markdown(f"## Versets contenant au moins l'un des mots choisis :")
                st.data_editor(select[['Sourate', 'Num_verset', 'Texte']].set_axis(['Sourate', 'Verset N°', 'Texte'], axis = 1),
                                use_container_width=True)
                
                if mode_recherche.startswith("OU"):
                    st.markdown(f"## Statistiques autour des mots choisis :")
                    
                    tableau, graph = st.columns([0.5, 0.5])

                    with tableau:
                        stats = []

                        if mots:
                            for mot in mots:

                                pattern = re.escape(mot)

                                # Nombre total d'occurrences
                                total_occ = select["Texte"].str.count(pattern, flags=re.IGNORECASE).sum()

                                # Versets contenant le mot
                                versets_mask = select["Texte"].str.contains(pattern, case=False, na=False)
                                nb_versets = versets_mask.sum()

                                # Sourates concernées
                                nb_sourates = select.loc[versets_mask, "index"].nunique()

                                stats.append({
                                    "Mot": mot,
                                    "Nb de sourates": int(nb_sourates),
                                    "Part": f"{round(int(nb_sourates) / 114 * 100, 2)} %",
                                    "Nb de versets": int(nb_versets),
                                    "Occurrences totales": int(total_occ)
                                })

                            stats_df = pd.DataFrame(stats)
                            st.dataframe(stats_df, use_container_width=True)

                            st.write("Interprétation :")
                            st.write(f"Le mot {stats_df["Mot"].iloc[0]} est présent dans {stats_df["Nb de sourates"].iloc[0]} sourates, soit {stats_df["Part"].iloc[0]} des 114 sourates. Il apparait {stats_df["Occurrences totales"].iloc[0]} fois dans l'ensemble du Coran.")
                        
                        with graph:

                            stats_df = stats_df.sort_values("Occurrences totales", ascending=True)
                            fig, ax = plt.subplots(figsize=(4, 2))

                            ax.barh(stats_df["Mot"], stats_df["Occurrences totales"])

                            ax.set_title("Nombre total d'occurrences par mot")

                            plt.tight_layout()

                            st.pyplot(fig)

            elif page == "📖 Lecture":

                for sourate, groupe in select.groupby("Sourate"):

                    st.markdown(f"## {sourate}")
                    st.divider()

                    # Tri correct des versets
                    groupe = groupe.sort_values("Num_verset", key=lambda x: x.astype(int))

                    for _, row in groupe.iterrows():
                        st.markdown(f"**{row['Num_verset']} -** {row['Texte']}")

                    st.markdown("---")
        else :
           print('\n --- Pas de résultat :( ---')
