import pandas as pd
import streamlit as st
from functools import partial
from pygwalker.api.streamlit import StreamlitRenderer
import plotly.express as px
import plotly.graph_objects as go
import uuid



FULLMONTHS = [
        "Ene", "Ene.1", "Ene 25", "Ene-25", "25 Ene", "25-Ene",
        "Jan", "Jan.1", "Jan 25", "Jan-25", "25 Jan", "25-Jan",
        "Feb", "Feb.1", "Feb 25", "Feb-25", "25 Feb", "25-Feb",
        "Mar", "Mar.1", "Mar 25", "Mar-25", "25 Mar", "25-Mar",
        "Abr", "Abr.1", "Abr 25", "Abr-25", "25 Abr", "25-Abr",
        "Apr", "Apr.1", "Apr 25", "Apr-25", "25 Apr", "25-Apr",
        "May", "May.1", "May 25", "May-25", "25 May", "25-May",
        "Jun", "Jun.1", "Jun 25", "Jun-25", "25 Jun", "25-Jun",
        "Jul", "Jul.1", "Jul 25", "Jul-25", "25 Jul", "25-Jul",
        "Ago", "Ago.1", "Ago 25", "Ago-25", "25 Ago", "25-Ago",
        "Aug", "Aug.1", "Aug 25", "Aug-25", "25 Aug", "25-Aug",
        "Sep", "Sep.1", "Sep 25", "Sep-25", "25 Sep", "25-Sep",
        "Oct", "Oct.1", "Oct 25", "Oct-25", "25 Oct", "25-Oct",
        "Nov", "Nov.1", "Nov 25", "Nov-25", "25 Nov", "25-Nov",
        "Dic", "Dic.1", "Dic 25", "Dic-25", "25 Dic", "25-Dic",
        "Dec", "Dec.1", "Dec 25", "Dec-25", "25 Dec", "25-Dec",
    ]
if "saved_files" not in st.session_state:
    st.session_state.saved_files = {}
#st.session_state.saved_files["nombre_del_archivo"] = pd.DataFrame()
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.dialog(
    title="Confirmar acción",
)
def confirmation_dialog(message, action=None):
    """
    Displays a confirmation dialog to the user.

    Args:
        message (str): The message to display in the dialog.

    Returns:
        bool: `True` if the user confirms, `False` otherwise.
    """
    st.write(message)
    c1, c2 = st.columns([1, 1])
    if c1.button(
        "Confirmar", icon=":material/check:", type="primary", use_container_width=True
    ):
        action() if action else None
    if c2.button("Cancelar", icon=":material/close:", use_container_width=True):
        st.rerun()


def group_by_quarter(data):
    """
    Groups the data by quarter and adds a column summing monthly values.

    Args:
        data (DataFrame): The data to group.

    Returns:
        dict: A dictionary of DataFrames grouped by quarter with added sum column.
    """
    fullmonths = FULLMONTHS
    quarters = {
        "Q1": ["Ene", "Feb", "Mar", "Jan", "Ene.1", "Feb.1", "Mar.1", "Jan.1", 
               "Jan 25", "Jan-25", "Feb 25", "Feb-25", "Mar 25", "Mar-25",
               "Ene 25", "Ene-25", "25 Ene", "25-Ene", "25 Feb", "25-Feb",
               "25 Mar", "25-Mar"],
        "Q2": ["Abr", "May", "Jun", "Apr", "Abr.1", "May.1", "Jun.1", "Apr.1",
               "Abr 25", "Abr-25", "May 25", "May-25", "Jun 25", "Jun-25",
               "25 Abr", "25-Abr", "25 May", "25-May", "25 Jun", "25-Jun"],
        "Q3": ["Jul", "Ago", "Sep", "Aug", "Jul.1", "Ago.1", "Sep.1", "Aug.1",
               "Jul 25", "Jul-25", "Ago 25", "Ago-25", "Sep 25", "Sep-25",
               "25 Jul", "25-Jul", "25 Ago", "25-Ago", "25 Sep", "25-Sep"],
        "Q4": ["Oct", "Nov", "Dic", "Dec", "Oct.1", "Nov.1", "Dic.1", "Dec.1",
               "Oct 25", "Oct-25", "Nov 25", "Nov-25", "Dic 25", "Dic-25",
               "25 Oct", "25-Oct", "25 Nov", "25-Nov", "25 Dic", "25-Dic"],
    }
    qs = {}

    for q, months in quarters.items():
        dq = [col for col in data.columns if any(m in col for m in months) or col not in fullmonths]
        if dq:
            quarter_df = data[dq]
            # Add a column summing monthly values
            month_cols = [col for col in quarter_df.columns if any(m in col for m in months)]
            quarter_df[f"{q}_Total"] = quarter_df[month_cols].sum(axis=1)
            qs[q] = quarter_df
    
    return qs



def save_file_to_session(data, name_of_file, selected_cols):
    st.session_state.saved_files[name_of_file] = (
        data[selected_cols] if selected_cols else data
    )
    st.toast("Archivo guardado con éxito", icon=":material/done:")
    st.rerun()


@st.cache_data(show_spinner=False)
def process_excel_data(file_path, sheet_name):
    """
    Reads an Excel file, processes the data, and performs calculations.

    Args:
        file_path (str): Path to the Excel file.
        sheet_name (str): Name of the sheet to process.

    Returns:
        dict: A dictionary containing processed dataframes and calculated totals.
    """
    # Load the workbook and sheet
    k = 0
    workbook = None
    while k < 10:
        

        workbook = pd.read_excel(file_path, skiprows=k, sheet_name=sheet_name)
        last_abl = None
        last_global_client_desc = None
        if "ABL" in workbook.columns or "Global Client DESC" in workbook.columns:
            if "ABL" not in workbook.columns:
                # Skip an additional row when renaming columns
                workbook = pd.read_excel(
                    file_path, skiprows=k + 1, sheet_name=sheet_name
                )
                workbook.rename(
                    columns={
                        #Renombrar las columnas según la planilla de Excel
                        "Unnamed: 0": "Tipo",
                        "Unnamed: 1": "Global Client Global Client ID",
                        "Unnamed: 2": "Global Client DESC",
                        "Unnamed: 3": "VM2",
                        "Unnamed: 4": "Prj Region",
                        "Unnamed: 5": "Project Project Id",
                        "Unnamed: 6": "Project Project Desc",
                        "Unnamed: 7": "Prj Type.",
                        "Unnamed: 8": "Offering A",
                        "Unnamed: 9": "Prj Offering",
                        "Unnamed: 10": "Prj Sub Offering",
                        "Unnamed: 11": "Prj Division Group Ou",
                        "Unnamed: 12": "Opp Nr. ID",
                        "Unnamed: 13": "Opp Nr. DESC",
                        "Unnamed: 14": "Client Type CRM.",
                        "Unnamed: 15": "Project Type CRM.",
                        "Unnamed: 16": "Stage CRM.",
                        "Unnamed: 17": "Prj Service Type",
                        "Unnamed: 18": "Prj Engagement Type",
                        "Unnamed: 19": "ABL",
                        "Unnamed: 20": "Total",
                    },
                    inplace=True,
                )
                # Remove the first row of data
                workbook = workbook.iloc[1:]
            else:
                for icol in ["TOTAL", "Q1", "Q2", "Q3", "Q4"]:
                    if icol in workbook.columns:
                        workbook.drop(columns=[icol], inplace=True)
                        
            # Skip rows exclusively for the first change in the "Tipo" column, excluding the first row
            if "Tipo" in workbook.columns:
                tipo_changes = workbook["Tipo"].ne(workbook["Tipo"].shift())
                skip_indices = tipo_changes[tipo_changes].index[1::2]  # Skip every second occurrence of a change
                skip_indices = skip_indices[skip_indices != 0]  # Exclude the first row
                workbook = workbook.drop(index=skip_indices).reset_index(drop=True)

            # Skip rows exclusively for the first change in the "Tipo" column, excluding the first row
            if "Tipo" in workbook.columns:
                tipo_changes = workbook["Tipo"].ne(workbook["Tipo"].shift())
                skip_indices = tipo_changes[tipo_changes].index[::2]  # Skip every second occurrence of a change
                skip_indices = skip_indices[skip_indices != 0]  # Exclude the first row
                workbook = workbook.drop(index=skip_indices).reset_index(drop=True)

            for row in workbook.iterrows():
                if "ABL" in workbook.columns:
                    if isinstance(row[1]["ABL"], str):
                        last_abl = row[1]["ABL"]
                    else:
                        workbook.at[row[0], "ABL"] = last_abl
                if "Global Client DESC" in workbook.columns:
                    if isinstance(row[1]["Global Client DESC"], str):
                        last_global_client_desc = row[1]["Global Client DESC"]
                    else:
                        workbook.at[row[0], "Global Client DESC"] = (
                            last_global_client_desc
                        )
            workbook.fillna(0, inplace=True)
            # drop duplicate columns

            return workbook
        k += 1

    return None


def choose_sheet_name(file_path):
    workbook = pd.ExcelFile(file_path)
    sheet_names = workbook.sheet_names
    sheet_name = st.selectbox("Select sheet", sheet_names)
    return sheet_name

def save_file_view():
    """
    Displays the view for saving a data file.
    """
    c1, c2 = st.columns([1, 2])

    file = c1.file_uploader("Upload file", type=["xlsx", "xls"])
    name_of_file = c1.text_input("Nombre del archivo", placeholder="Outlook 2 + 10")
    if file is not None:
        with c1:
            sheet_name = choose_sheet_name(file)
        with c2:
            datatabs = st.tabs(["Datos Originales", "Selección de Datos para las Proyecciones"])
            with st.spinner("Procesando archivo..."):
                data = process_excel_data(file, sheet_name)
            if data is not None:
                datatabs[0].write(data)

        with c1:
            if data is not None:
                dfcols = data.columns
                selected_cols = []
                selected_values = []

                # Column selection
                with datatabs[1].popover(
                    "Columnas a seleccionar",
                    help="Selecciona las columnas que deseas guardar",
                    icon=":material/add_box:",
                    use_container_width=True,
                ):
                    selected_cols = st.multiselect(
                        "Select columns", dfcols, help="Selecciona las columnas a guardar en el archivo"
                    )

                # Row selection based on the "Tipo" column
                if "Tipo" in data.columns:
                    with datatabs[1].popover(
                        "Tipo de valor a seleccionar",
                        help="Selecciona las filas basadas en los valores de la columna 'Tipo'",
                        icon=":material/filter_list:",
                        use_container_width=True,
                    ):
                        unique_values = data["Tipo"].unique()
                        selected_values = st.multiselect(
                            "Select the Type of values", unique_values, help="Selecciona los valores de 'Tipo' para filtrar las filas"
                        )

                # Combine filters
                if selected_cols and selected_values:
                    filtered_data = data.loc[data["Tipo"].isin(selected_values), selected_cols]
                    datatabs[1].write(filtered_data)
                elif selected_cols:
                    filtered_data = data[selected_cols]
                    datatabs[1].write(filtered_data)
                elif selected_values:
                    filtered_data = data[data["Tipo"].isin(selected_values)]
                    datatabs[1].write(filtered_data)
                else:
                    datatabs[1].warning(
                        "Selecciona las columnas y/o filas necesarias para realizar la comparación, si no seleccionas ninguna se mostrará el archivo completo",
                        icon=":material/warning:",
                    )

                if not selected_cols and not selected_values:
                    st.warning("No se han seleccionado columnas o filas, se guardará el archivo completo", icon=":material/release_alert:")
            else:
                c2.error(
                    "No se encontró una estructura válida en el archivo, por favor asegúrate de que el archivo tenga la estructura correcta.\n Si crees que es un error, por favor contacta a soporte",
                    icon=":material/error:",
                )
                st.stop()
        if c1.button(
            "Guardar",
            icon=":material/insert_drive_file:",
            disabled=not file or not name_of_file,
            use_container_width=True,
            type="primary",
            help="Nombre al archivo para guardarlo y poder utilizarlo en el futuro, recuerda que los meses son obligatorios y solo se considerarán los datos para una sola",
        ):
            if name_of_file in st.session_state.saved_files.keys():
                confirmation_dialog(
                    "¿Estás seguro de sobreescribir el archivo?",
                    partial(save_file_to_session, filtered_data, name_of_file, selected_cols),
                )
            else:
                save_file_to_session(filtered_data, name_of_file, selected_cols)

def display_data_analysis():
    """
    Displays the view for analyzing data.
    """
    dfselect = st.selectbox("Selecciona una proyección",
                             list(st.session_state.saved_files.keys()))
    @st.cache_resource
    def load_pyw(dfselect):
        pygapp = StreamlitRenderer(st.session_state.saved_files[dfselect],default_tab='data')
        return pygapp

    pygapp = load_pyw(dfselect)
    pygapp.explorer()


def pie_of_quarter(q : pd.DataFrame):
    """
    Creates a pie chart for the selected quarter.

    Args:
        q (str): The quarter to create a pie chart for.
    """
    if "Global Client DESC" not in q.columns:
        return None
    fullmonths = FULLMONTHS
    monts = [col for col in q.columns if any(m in col for m in fullmonths)]
    GCQ = q.groupby(["Global Client DESC"])
    ddf = []
    for gc, df in GCQ:
        ddf.append({'Global Client DESC':gc,'Suma':df[monts].sum().sum()})

    df = pd.DataFrame(ddf)
    fig = px.pie(df, values='Suma', names='Global Client DESC', title="Proyección por Cliente")
    return fig


def area_of_quarter(q : pd.DataFrame):
    """
    Creates an area chart for the selected quarter.

    Args:
        q (str): The quarter to create an area chart for.
    """
    if "Project Project Desc" not in q.columns:
        return None
    fullmonths = FULLMONTHS
    monts = [col for col in q.columns if any(m in col for m in fullmonths)]
    serie = []
    for row in q.iterrows():
        serie.append({'Project Project Desc':str(row[1]['Project Project Desc']),'Suma':row[1][monts].sum()})

    df = pd.DataFrame(serie)
    # Change the type of the Project Project Id to string
    fig = px.area(df, x='Project Project Desc', y='Suma', title="Proyección por Proyecto")
    return fig

def create_plots_of_quarter(q : pd.DataFrame,proy:str):
    """
    Creates plots for the selected quarter.

    Args:
        q (str): The quarter to create plots for.
    """    
    pie = pie_of_quarter(q)
    area = area_of_quarter(q)
    if pie is not None:
        st.plotly_chart(pie,use_container_width=True, key=f"{proy}_pie_{uuid.uuid4()}")
    if area is not None:
        st.plotly_chart(area,use_container_width=True, key=f"{proy}_area_{uuid.uuid4()}")

def create_plots_of_difference_q(q : pd.DataFrame,proy:str):
    """
    Creates plots for the selected quarter.

    Args:
        q (str): The quarter to create plots for.
    """    
    area = area_of_quarter(q)
    if area is not None:
        st.plotly_chart(area,use_container_width=True, key=f"{proy}_area_{uuid.uuid4()}")


def create_plots_of_quarters(qs : dict):
    """
    Creates plots for the selected quarters.

    Args:
        qs (dict): The quarters to create plots for.
    """
    months = FULLMONTHS
    qss = []
    pseries = []
    for q, df in qs.items():
        cls = [col for col in df.columns if any(m in col for m in months)]
        qss.append({'Quarter':q,'Suma':df[cls].sum().sum()})
        if 'Project Project Desc' in df.columns or 'Project Project Id' in df.columns:
            d = []
            for row in df.iterrows():
                if 'Project Project Desc' in df.columns:
                    d.append({'Project Project Desc':row[1]['Project Project Desc'],'Suma':row[1][cls].sum()})
                else:
                    d.append({'Project Project Desc':row[1]['Project Project Id'],'Suma':row[1][cls].sum()})
            pseries.append({'Quarter':q,'Data':pd.DataFrame(d)})            
            
    
    df = pd.DataFrame(qss)
    fig = px.pie(df, values='Suma', names='Quarter', title="Proyección por Trimestre")
    c1, c2 = st.columns([1, 1])
    c1.plotly_chart(fig,use_container_width=True,key=f"quarters_{uuid.uuid4()}")
    if pseries:
        areafig = go.Figure()
        for ps in pseries:
            areafig.add_trace(go.Bar(x=ps['Data']['Project Project Desc'],y=ps['Data']['Suma'],name=ps['Quarter']))
            
        areafig.update_layout(barmode='group',title="Proyección por Proyecto")

        c2.plotly_chart(areafig,use_container_width=True,key=f"quarters_area_{uuid.uuid4()}")

        
def compare_files():
    """
    Displays the view for comparing data files.
    """
    c1, c2 = st.columns([1, 3])
    file_current = c1.selectbox("Selecciona la proyección actual",
                                list(st.session_state.saved_files.keys()))
    file_previous = c1.selectbox("Selecciona la proyección anterior",
                                 list(st.session_state.saved_files.keys()))
    if file_current == file_previous:
        c1.error("Las proyecciones seleccionadas son iguales, por favor selecciona proyecciones diferentes")
        st.stop()

    
    g1 = group_by_quarter(st.session_state.saved_files[file_current])
    g2 = group_by_quarter(st.session_state.saved_files[file_previous])

    tbs = c2.tabs(["Proyección Actual", "Proyección Anterior", "Diferencias Por Proyecto", "Diferencias Por Cliente"])
    with tbs[0].container(height=500):
        total_months = {}
        total_quarters = {}
        total_all_projects = 0

        for q, df in g1.items():
            with st.popover(f"{q} - {file_current}", use_container_width=True):
                qabs = st.tabs(["Datos", "Gráficos"])
                qabs[0].write(df.style.format({col: "${:,.2f}" for col in df.columns if col in FULLMONTHS or "Total" in col}))
                with qabs[1]:
                    create_plots_of_quarter(df, 'current')
            # Collect total values for each quarter
            total_col = f"{q}_Total"
            if total_col in df.columns:
                total_quarters[q] = df[total_col].sum()
                total_all_projects += df[total_col].sum()

            # Collect total values for each month that exists in the current dataframe
            for month in FULLMONTHS:
                if month in df.columns:
                    if month not in total_months:
                        total_months[month] = 0
                    total_months[month] += df[month].sum()

        # Add popover for total sums
        with st.popover("Todos los Proyectos por Mes, Trimestre y Total", use_container_width=True):
            # Create dataframes for months and quarters
            total_months_df = pd.DataFrame({
                "Mes": list(total_months.keys()),
                "Total": list(total_months.values())
            })
            total_quarters_df = pd.DataFrame({
                "Trimestre": list(total_quarters.keys()),
                "Total": list(total_quarters.values())
            })

            # Display dataframes and total in a qab called "Datos"
            qab = st.tabs(["Datos", "Gráficos"])
            with qab[0]:
                st.write("Totales por Mes")
                st.dataframe(total_months_df.style.format({"Total": "${:,.2f}"}))
                st.write("Totales por Trimestre")
                st.dataframe(total_quarters_df.style.format({"Total": "${:,.2f}"}))
                st.metric("Suma Total de Todos los Proyectos", f"${total_all_projects:,.2f}")

            with qab[1]:  # Add a new tab for "Gráficos"
                # Calculate percentage for each month
                total_months_df["Porcentaje"] = (total_months_df["Total"] / total_months_df["Total"].sum()) * 100

                # Change graph for total_months_df to a line chart with percentages
                fig_months = px.line(
                    total_months_df,
                    x="Mes",
                    y="Total",
                    text="Porcentaje",  # Add percentage as text on nodes
                    title="Totales por Mes",
                    labels={"Mes": "Mes", "Total": "Total"}
                )
                fig_months.update_traces(
                    mode="lines+markers+text",  # Show lines, markers, and text
                    textposition="top center",  # Position text above nodes
                    texttemplate='%{text:.2f}%'  # Format percentage
                )
                st.plotly_chart(fig_months, use_container_width=True)
            
        create_plots_of_quarters(g1)
            
    with tbs[1].container(height=500):
        total_months_previous = {}
        total_quarters_previous = {}
        total_all_projects_previous = 0

        for q, df in g2.items():
            with st.popover(f"{q} - {file_previous}", use_container_width=True):
                qabs = st.tabs(["Datos", "Gráficos"])
                qabs[0].write(df.style.format({col: "${:,.2f}" for col in df.columns if col in FULLMONTHS or "Total" in col}))
                with qabs[1]:
                    create_plots_of_quarter(df, 'previous')
            # Collect total values for each quarter
            total_col = f"{q}_Total"
            if total_col in df.columns:
                total_quarters_previous[q] = df[total_col].sum()
                total_all_projects_previous += df[total_col].sum()

            # Collect total values for each month that exists in the previous dataframe
            for month in FULLMONTHS:
                if month in df.columns:
                    if month not in total_months_previous:
                        total_months_previous[month] = 0
                    total_months_previous[month] += df[month].sum()

        # Add popover for total sums
        with st.popover("Todos los Proyectos por Mes, Trimestre y Total", use_container_width=True):
            # Create dataframes for months and quarters
            total_months_previous_df = pd.DataFrame({
                "Mes": list(total_months_previous.keys()),
                "Total": list(total_months_previous.values())
            })
            total_quarters_previous_df = pd.DataFrame({
                "Trimestre": list(total_quarters_previous.keys()),
                "Total": list(total_quarters_previous.values())
            })
            # Display dataframes and total
            qab = st.tabs(["Datos", "Gráficos"])
            with qab[0]:  # Move dataframes to the "Datos" tab
                st.write("Totales por Mes")
                st.dataframe(total_months_previous_df.style.format({"Total": "${:,.2f}"}))
                st.write("Totales por Trimestre")
                st.dataframe(total_quarters_previous_df.style.format({"Total": "${:,.2f}"}))
                st.metric("Suma Total de Todos los Proyectos (Anterior)", f"${total_all_projects_previous:,.2f}")

            with qab[1]:  # Move graphs to the "Gráficos" tab
                # Change graph for total_months_previous_df to a line chart with percentages
                total_months_previous_df["Porcentaje"] = (total_months_previous_df["Total"] / total_months_previous_df["Total"].sum()) * 100

                fig_months_previous = px.line(
                    total_months_previous_df,
                    x="Mes",
                    y="Total",
                    text="Porcentaje",  # Add percentage as text on nodes
                    title="Totales por Mes (Proyección Anterior)",
                    labels={"Mes": "Mes", "Total": "Total"}
                )
                fig_months_previous.update_traces(
                    mode="lines+markers+text",  # Show lines, markers, and text
                    textposition="top center",  # Position text above nodes
                    texttemplate='%{text:.2f}%'  # Format percentage
                )
                st.plotly_chart(fig_months_previous, use_container_width=True)

            
        create_plots_of_quarters(g2)
                
    with tbs[2].container(height=500):
        # Convert "ABL" column values to uppercase
        df_current = st.session_state.saved_files[file_current]
        df_previous = st.session_state.saved_files[file_previous]
        
        if "ABL" in df_current.columns:
            df_current["ABL"] = df_current["ABL"].str.upper()
        if "ABL" in df_previous.columns:
            df_previous["ABL"] = df_previous["ABL"].str.upper()
        
        # Merge the dataframes for "Diferencias por Proyecto"
        # Exclude month-related columns from the merge keys
        month_columns = [col for col in df_current.columns if any(m in col for m in FULLMONTHS)]
        merge_keys = [col for col in df_current.columns if col not in month_columns and col in df_previous.columns]

        merged_df = pd.merge(
            df_current, df_previous, 
            on=merge_keys, 
            how="outer", 
            suffixes=("_current", "_previous")
        ).fillna(0)
        
        # Add columns for differences by quarter
        quarter_months = {
            "Q1": ["Jan 25", "Feb 25", "Mar 25", "Feb-25", "Mar-25"],
            "Q2": ["Apr 25", "May 25", "Jun 25", "Apr-25", "May-25", "Jun-25"],
            "Q3": ["Jul 25", "Aug 25", "Sep 25", "Jul-25", "Aug-25", "Sep-25"],
            "Q4": ["Oct 25", "Nov 25", "Dec 25", "Oct-25", "Nov-25", "25-Dec"]
        }
        
        for quarter, months in quarter_months.items():
            current_sum = merged_df[[f"{month}_current" for month in months if f"{month}_current" in merged_df.columns]].sum(axis=1)
            previous_sum = merged_df[[f"{month}_previous" for month in months if f"{month}_previous" in merged_df.columns]].sum(axis=1)
            merged_df[quarter] = current_sum - previous_sum

        # Add a total column summing all quarter differences
        merged_df["TOTAL"] = merged_df[["Q1", "Q2", "Q3", "Q4"]].sum(axis=1)
        
        # Display the merged dataframe in a popover with tabs
        with st.popover("Diferencias Trimestrales Todos los Proyectos", use_container_width=True):
            qab = st.tabs(["Datos", "Gráficos"])
            with qab[0]:
                st.write("Detalle Todos los Proyectos y Diferencias Trimestrales y Total")
                def highlight_quarters(val):
                    if val > 0:
                        return 'background-color: green; color: white;'
                    elif val < 0:
                        return 'background-color: red; color: white;'
                    return ''

                st.dataframe(
                    merged_df.style.format(
                        {col: "${:,.2f}" for col in merged_df.columns if merged_df[col].dtype in ['float64', 'int64']}
                    ).applymap(
                        highlight_quarters, subset=["Q1", "Q2", "Q3", "Q4", "TOTAL"]
                    )
                )
            with qab[1]:
                st.write("Gráfico de Diferencias Totales por Proyecto (Q1)")
                # Exclude projects with Q1 variation of 0
                filtered_merged_df_q1 = merged_df[merged_df["Q1"] != 0].sort_values(by="Q1", ascending=True)
                # Add a bar chart for variations by project sorted by "Q1"
                fig_q1 = px.bar(
                    filtered_merged_df_q1,
                    x="Project Project Desc",
                    y="Q1",
                    title="Variaciones por Proyecto en Q1 (Distintas de 0)",
                    labels={"Q1": "Variación Q1", "Project Project Desc": "Proyecto"}
                )
                fig_q1.update_traces(marker_color=[
                    "green" if val > 0 else "red" for val in filtered_merged_df_q1["Q1"]
                ])
                st.plotly_chart(fig_q1, use_container_width=True)

                st.write("Gráfico de Diferencias Totales por Proyecto (Q2)")
                # Exclude projects with Q2 variation of 0
                filtered_merged_df_q2 = merged_df[merged_df["Q2"] != 0].sort_values(by="Q2", ascending=True)
                # Add a bar chart for variations by project sorted by "Q2"
                fig_q2 = px.bar(
                    filtered_merged_df_q2,
                    x="Project Project Desc",
                    y="Q2",
                    title="Variaciones por Proyecto en Q2 (Distintas de 0)",
                    labels={"Q2": "Variación Q2", "Project Project Desc": "Proyecto"}
                )
                fig_q2.update_traces(marker_color=[
                    "green" if val > 0 else "red" for val in filtered_merged_df_q2["Q2"]
                ])
                st.plotly_chart(fig_q2, use_container_width=True)

                st.write("Gráfico de Diferencias Totales por Proyecto (Q3)")
                # Exclude projects with Q3 variation of 0
                filtered_merged_df_q3 = merged_df[merged_df["Q3"] != 0].sort_values(by="Q3", ascending=True)
                # Add a bar chart for variations by project sorted by "Q3"
                fig_q3 = px.bar(
                    filtered_merged_df_q3,
                    x="Project Project Desc",
                    y="Q3",
                    title="Variaciones por Proyecto en Q3 (Distintas de 0)",
                    labels={"Q3": "Variación Q3", "Project Project Desc": "Proyecto"}
                )
                fig_q3.update_traces(marker_color=[
                    "green" if val > 0 else "red" for val in filtered_merged_df_q3["Q3"]
                ])
                st.plotly_chart(fig_q3, use_container_width=True)

                st.write("Gráfico de Diferencias Totales por Proyecto (Q4)")
                # Exclude projects with Q4 variation of 0
                filtered_merged_df_q4 = merged_df[merged_df["Q4"] != 0].sort_values(by="Q4", ascending=True)
                # Add a bar chart for variations by project sorted by "Q4"
                fig_q4 = px.bar(
                    filtered_merged_df_q4,
                    x="Project Project Desc",
                    y="Q4",
                    title="Variaciones por Proyecto en Q4 (Distintas de 0)",
                    labels={"Q4": "Variación Q4", "Project Project Desc": "Proyecto"}
                )
                fig_q4.update_traces(marker_color=[
                    "green" if val > 0 else "red" for val in filtered_merged_df_q4["Q4"]
                ])
                st.plotly_chart(fig_q4, use_container_width=True)

                st.write("Gráfico de Diferencias Totales por Proyecto (TOTAL)")
                # Exclude projects with TOTAL variation of 0
                filtered_merged_df_total = merged_df[merged_df["TOTAL"] != 0].sort_values(by="TOTAL", ascending=True)
                # Add a bar chart for variations by project sorted by "TOTAL"
                fig_total = px.bar(
                    filtered_merged_df_total,
                    x="Project Project Desc",
                    y="TOTAL",
                    title="Variaciones por Proyecto en TOTAL (Distintas de 0)",
                    labels={"TOTAL": "Variación TOTAL", "Project Project Desc": "Proyecto"}
                )
                fig_total.update_traces(marker_color=[
                    "green" if val > 0 else "red" for val in filtered_merged_df_total["TOTAL"]
                ])
                st.plotly_chart(fig_total, use_container_width=True)

        
        # Add a popover for differences by month and quarter
        with st.popover("Diferencias por Mes y Trimestre Todos los Proyectos", use_container_width=True):
            # Calculate monthly differences
            monthly_differences = total_months_df.set_index("Mes") - total_months_previous_df.set_index("Mes")
            monthly_differences.reset_index(inplace=True)
            monthly_differences.rename(columns={"Total": "Diferencia"}, inplace=True)

            # Drop the "Porcentaje" column if it exists
            monthly_differences = monthly_differences.loc[:, ~monthly_differences.columns.isin(["Porcentaje"])]

            # Calculate quarterly differences
            quarterly_differences = total_quarters_df.set_index("Trimestre") - total_quarters_previous_df.set_index("Trimestre")
            quarterly_differences.reset_index(inplace=True)
            quarterly_differences.rename(columns={"Total": "Diferencia"}, inplace=True)

            # Calculate total difference
            total_difference = total_all_projects - total_all_projects_previous

            # Display differences with tabs for data and graphs
            qab = st.tabs(["Datos", "Gráficos"])
            with qab[0]:
                st.write("Diferencias por Mes")
                st.dataframe(
                    monthly_differences.style.format(
                        {"Diferencia": "${:,.2f}"}
                    )
                )
                
                st.write("Diferencias por Trimestre")
                st.dataframe(
                    quarterly_differences.style.format(
                        {"Diferencia": "${:,.2f}"}
                    )
                )

                st.data_editor(
                    pd.DataFrame({"Diferencia Total": [total_difference]}),
                    column_config={
                        "Diferencia Total": st.column_config.NumberColumn(
                            format="$%.2f",
                            help="Diferencia Total en formato monetario"
                        )
                    },
                    hide_index=True
                )
            with qab[1]:
                st.write("Gráfico de Diferencias por Mes")
                fig_monthly = px.area(
                    monthly_differences,
                    x="Mes",
                    y="Diferencia",
                    title="Diferencias por Mes",
                    labels={"Diferencia": "Diferencia", "Mes": "Mes"}
                )
                fig_monthly.update_traces(
                    line_color="blue",
                    fill="tozeroy",
                    showlegend=False
                )
                st.plotly_chart(fig_monthly, use_container_width=True)

                st.write("Gráfico de Diferencias por Trimestre")
                fig_quarterly = px.area(
                    quarterly_differences,
                    x="Trimestre",
                    y="Diferencia",
                    title="Diferencias por Trimestre",
                    labels={"Diferencia": "Diferencia", "Trimestre": "Trimestre"}
                )
                fig_quarterly.update_traces(
                    line_color="blue",
                    fill="tozeroy",
                    showlegend=False
                )
                st.plotly_chart(fig_quarterly, use_container_width=True)
        
    with tbs[3].container(height=500):
        # Add "Var Por Cte" tabs directly
        tabs = st.tabs(["Datos", "Gráficos"])
        client_projections_current = []
        client_projections_previous = []

        for q, df in g1.items():
            if "Global Client DESC" in df.columns and f"{q}_Total" in df.columns:
                client_data = pd.DataFrame({
                    "Cliente": df["Global Client DESC"],
                    f"{q} - Ahora": df[f"{q}_Total"]
                })
                client_projections_current.append(client_data)

        for q, df in g2.items():
            if "Global Client DESC" in df.columns and f"{q}_Total" in df.columns:
                client_data = pd.DataFrame({
                    "Cliente": df["Global Client DESC"],
                    f"{q} - Anterior": df[f"{q}_Total"]
                })
                client_projections_previous.append(client_data)

        # Combine and group client projections dataframes
        if client_projections_current or client_projections_previous:
            combined_current = pd.concat(client_projections_current, ignore_index=True) if client_projections_current else pd.DataFrame()
            combined_previous = pd.concat(client_projections_previous, ignore_index=True) if client_projections_previous else pd.DataFrame()

            grouped_current = combined_current.groupby("Cliente", as_index=False).sum() if not combined_current.empty else pd.DataFrame()
            grouped_previous = combined_previous.groupby("Cliente", as_index=False).sum() if not combined_previous.empty else pd.DataFrame()

            # Merge current and previous projections
            merged_projections = pd.merge(grouped_current, grouped_previous, on="Cliente", how="outer").fillna(0)

            # Add variance columns for each quarter
            for q in ["Q1", "Q2", "Q3", "Q4"]:
                if f"{q} - Ahora" in merged_projections.columns and f"{q} - Anterior" in merged_projections.columns:
                    merged_projections[f"{q} - Var"] = merged_projections[f"{q} - Ahora"] - merged_projections[f"{q} - Anterior"]

            # Add "Total Var" column
            variance_columns = [f"{q} - Var" for q in ["Q1", "Q2", "Q3", "Q4"] if f"{q} - Var" in merged_projections.columns]
            if variance_columns:
                merged_projections["Total Var"] = merged_projections[variance_columns].sum(axis=1)

            # Show data in the "Datos" tab
            with tabs[0]:
                st.write("Proyecciones por Cliente (Actual, Anterior, Variación y Total Variación)")
                def highlight_variation(val):
                    if val > 0:
                        return 'background-color: green; color: white;'
                    elif val < 0:
                        return 'background-color: red; color: white;'
                    return ''
                
                styled_df = merged_projections.style.format({
                    col: "${:,.2f}" for col in merged_projections.columns if merged_projections[col].dtype in ['float64', 'int64']
                }).applymap(highlight_variation, subset=["Total Var", "Q1 - Var", "Q2 - Var", "Q3 - Var", "Q4 - Var"])
                
                st.dataframe(styled_df)

            # Show graphs in the "Gráficos" tab
            with tabs[1]:
                if "Total Var" in merged_projections.columns:
                    fig = px.bar(
                        merged_projections,
                        x="Cliente",
                        y="Total Var",
                        title="Variación Total por Cliente",
                        labels={"Total Var": "Variación Total", "Cliente": "Cliente"}
                    )
                    fig.update_traces(marker_color=[
                        "green" if val > 0 else "red" for val in merged_projections["Total Var"]
                    ])
                    st.plotly_chart(fig, use_container_width=True)

                # Create a graph for each quarter
                for q in ["Q1", "Q2", "Q3", "Q4"]:
                    if f"{q} - Var" in merged_projections.columns:
                        quarter_fig = px.bar(
                            merged_projections,
                            x="Cliente",
                            y=f"{q} - Var",
                            title=f"Variación por Cliente - {q}",
                            labels={f"{q} - Var": f"Variación {q}", "Cliente": "Cliente"}
                        )
                        quarter_fig.update_traces(marker_color=[
                            "green" if val > 0 else "red" for val in merged_projections[f"{q} - Var"]
                        ])
                        st.plotly_chart(quarter_fig, use_container_width=True)


    

mcmap = {
    "upload_file": ":material/cloud_upload: Crear Proyección",
    "data_analysis": ":material/insights: Analizar Proyecciones",
    "compare_files": ":material/difference: Comparar Proyecciones",
}

mcontrol = st.segmented_control(
    "Seleccione una acción",
    list(mcmap.keys()),
    format_func=lambda x: mcmap[x],
    label_visibility="collapsed",
    key="main_control",
)

if mcontrol == "upload_file":
    save_file_view()
elif mcontrol == "data_analysis":
    display_data_analysis()
elif mcontrol == "compare_files":
    compare_files()

# sheet_name = '1.Detalle2+10vs3+9'  # Replace with the actual sheet name
