import streamlit as st
import shelve
from datetime import datetime
from openai import OpenAI

openai = OpenAI(api_key="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")

priority_icons = {
    "Alta": "🔴",
    "Media": "🟡",
    "Baja": "🟢",
    "Urgente": "🔵",
}

status_icons = {
    "Completada": "✅",
    "En proceso": "🚧",
    "Finalizada": "🎉",
    "En revisión": "🔍",
    "Sin estado": "❓",
    "En espera": "⌛",
}

task_card_style = """
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 10px;
"""

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_task(nombre, descripcion, fecha_limite, prioridad, estado, recursos, tiempo_estimado):
    if not st.session_state.tasks:
        task_id = 1
    else:
        task_id = st.session_state.tasks[-1]['idtask'] + 1

    task = {
        'idtask': task_id,
        'nombre': nombre,
        'descripcion': descripcion,
        'fecha_limite': fecha_limite,
        'prioridad': prioridad,
        'estado': estado,
        'recursos': recursos,
        'tiempo_estimado': tiempo_estimado,
        'timestamp': get_timestamp()
    }
    st.session_state.tasks.append(task)

    # Organizar las tareas después de agregar una nueva tarea
    prompt = get_prompt(st.session_state.tasks)
    organized_task_ids = organize_tasks(prompt)
    update_task_order(organized_task_ids)

def delete_task(task_id):
    st.session_state.tasks = [task for task in st.session_state.tasks if task['idtask'] != task_id]

def edit_task(task_id, new_name, new_description, new_fecha_limite, new_prioridad, new_estado, new_recursos, new_tiempo_estimado):
    for task in st.session_state.tasks:
        if task['idtask'] == task_id:
            task['nombre'] = new_name
            task['descripcion'] = new_description
            task['fecha_limite'] = new_fecha_limite
            task['prioridad'] = new_prioridad
            task['estado'] = new_estado
            task['recursos'] = new_recursos
            task['tiempo_estimado'] = new_tiempo_estimado
            task['timestamp'] = get_timestamp()

def load_tasks():
    with shelve.open('tasks.db') as storage:
        return storage.get('tasks', [])

def save_tasks(tasks):
    with shelve.open('tasks.db', writeback=True) as storage:
        storage['tasks'] = tasks

def get_prompt(tasks):
    tasks_json = [{'idtask': task['idtask'], 'prioridad': task['prioridad'], 'tiempo_estimado': task['tiempo_estimado'], 'fecha_limite': task['fecha_limite']} for task in tasks]
    return f"Organizar las siguientes tareas en orden según la prioridad, tiempo estimado y fecha límite:\n{tasks_json}"

def organize_tasks(prompt):
    response = openai.chat.completions.create(
        model="whisper-1",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )

    organized_task_ids = response['choices'][0]['message']['content'].split("\n")
    return [int(task_id) for task_id in organized_task_ids if task_id.isdigit()]


def update_task_order(organized_task_ids):
    organized_tasks = [t for t_id in organized_task_ids for t in st.session_state.tasks if t['idtask'] == t_id]
    st.session_state.tasks = organized_tasks

def main():
    st.title("App OTasks")

    if 'tasks' not in st.session_state:
        st.session_state.tasks = load_tasks()

    # Formulario para agregar tareas en el sidebar
    st.sidebar.subheader("Añadir Tarea:")
    name = st.sidebar.text_input("Nombre de la tarea:")
    description = st.sidebar.text_area("Descripción de la tarea:")
    fecha_limite = st.sidebar.date_input("Fecha límite", min_value=datetime.now())
    prioridad = st.sidebar.selectbox("Prioridad", ["Alta", "Media", "Baja", "Urgente"])
    estado = st.sidebar.selectbox("Estado", ["Completada", "En proceso", "Finalizada", "En revisión", "Sin estado", "En espera"])
    recursos = st.sidebar.text_input("Recursos de la tarea:")
    tiempo_estimado = st.sidebar.number_input("Tiempo estimado (horas)", min_value=0, step=1)

    if st.sidebar.button("Agregar Tarea"):
        if name and description:
            add_task(name, description, fecha_limite, prioridad, estado, recursos, tiempo_estimado)
            st.sidebar.success("Tarea agregada exitosamente.")

    # Obtener todas las tareas de la sesión
    tasks = st.session_state.tasks

    for task in tasks:
        st.write(f"**{task['nombre']}**")
        st.write(f"{task['descripcion']}")
        new_fecha_limite_key = f"new_fecha_limite_{task['idtask']}"
        new_fecha_limite = st.date_input("Nueva fecha límite:", min_value=datetime.now(), key=new_fecha_limite_key)
        st.write(f"P: {task['prioridad']} {priority_icons[task['prioridad']]} | "
                 f"E: {task['estado']} {status_icons[task['estado']]} | "
                 f"Recursos: {task['recursos']} | "
                 f"Tiempo estimado: {task['tiempo_estimado']} horas")
        st.write(f"Última modificación: {task['timestamp']}")

        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button(f"🗑️ Eliminar", key=f"delete_{task['idtask']}"):
                delete_task(task['idtask'])
                st.success(f"Tarea {task['idtask']} eliminada exitosamente.")
                st.experimental_rerun()

        with col2:
            edit_expander = st.expander(f"✏️")
            with edit_expander:
                new_name = st.text_input("Nuevo nombre:", task['nombre'])
                new_description = st.text_area("Nueva descripción:", task['descripcion'])
                new_fecha_limite = st.date_input("Nueva fecha límite:", min_value=datetime.now())
                new_prioridad = st.selectbox("Nueva prioridad:", ["Alta", "Media", "Baja", "Urgente"], index=prioridad.index(task['prioridad']) if task['prioridad'] in prioridad else 0)
                new_estado = st.selectbox("Nuevo estado:", ["Completada", "En proceso", "Finalizada", "En revisión", "Sin estado", "En espera"], index=estado.index(task['estado']) if task['estado'] in estado else 0)
                new_recursos = st.text_input("Nuevos recursos de la tarea:", value=task['recursos'])
                new_tiempo_estimado = st.number_input("Nuevo tiempo estimado (horas):", min_value=0, step=1, value=task['tiempo_estimado'])

                organize_button_key = f"organize_button_{task['idtask']}"
                if st.button("Organizar tareas", key=organize_button_key):
                    prompt = get_prompt(st.session_state.tasks)
                    organized_task_ids = organize_tasks(prompt)
                    organized_tasks = [t for t_id in organized_task_ids for t in st.session_state.tasks if t['idtask'] == t_id]
                    st.session_state.tasks = organized_tasks
                    st.success("Tareas organizadas exitosamente.")
                    st.experimental_rerun()

                save_changes_button_key = f"save_changes_button_{task['idtask']}"
                if st.button("Guardar cambios", key=save_changes_button_key):
                    edit_task(task['idtask'], new_name, new_description, new_fecha_limite, new_prioridad, new_estado, new_recursos, new_tiempo_estimado)
                    st.success(f"Tarea {task['idtask']} editada exitosamente.")
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
