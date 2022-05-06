#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as db
import PySimpleGUI as sg
import copy
import numpy as np
import matplotlib.pyplot as plt

Version = 'Версия 1.0 05.2022'
Developed = ' Соловьев М.Е. me_s@mail.ru'
DBfilename = 'composits.db'

def get_data(con,table: str) -> dict:
    cur = con.cursor().execute(f'SELECT * FROM {table}')
    data = [list(line) for line in cur.fetchall()]
    headers = list(next(zip(*cur.description)))
    return {'headers': headers, 'data': data}

def add_rec(db, table_name, field_names, field_vals):
    cur = db.cursor()
    sql_stm = "INSERT INTO "+table_name+" "+field_names
    num_fields = len(field_vals)
    val = " VALUES ("+"?,"*(num_fields-1)+"?) "
    sql_stm += val
    cur.execute(sql_stm,field_vals)
    db.commit()
    sql_stm = "SELECT * FROM "+table_name
    cur.execute(sql_stm)
    rows = cur.fetchall()
    return rows[-1]


def set_data(con, table: str, data: list) -> None:
    cur = con.cursor()
    column_count = len(data)
    cur.execute(f'INSERT INTO {table} VALUES (?{", ?" * (column_count - 1)})', data)
    con.commit()

def save_results(data):
    with open("results.txt", 'a') as f:
        f.write(data)

    sg.popup('Результаты сохранены в файле results.txt')

    
def composition_window():
    conn = db.connect(database=DBfilename)
    cur = conn.cursor()

    table = 'Composit_Descr'
    sql_stm = "SELECT Composition_ID, Composition_Name, Composition_Descr FROM "+table
    cur.execute(sql_stm)
    compositions = cur.fetchall()
    compositions_headings = ['ID','Наименование','Описание']
    results =''
    def recipy_choose(rec_ID):
        fields = "Composit_Descr.Composition_Name, Ingredients.Ingr_Name, Composit_Rec.Mass_PHR " 
        recipy=cur.execute("select " +fields+ "  from Composit_Descr, Ingredients, Composit_Rec where Composit_Descr.Composition_ID=Composit_Rec.Composition_ID and Ingredients.Ingr_ID=Composit_Rec.Ingr_ID and Composit_Rec.Composition_ID = " + str(rec_ID))
        rec_lst = []
        for row in recipy:
            rec_lst.append(list(row)[1:])
        return(rec_lst)
        
    def composition_choose(rec_ID):
        fields = "Composit_Descr.Composition_Name, Ingredients.Ingr_Name, Ingredients.Ingr_Descr, Ingredients.rho_field, Ingredients.HV_field, Ingredients.lamb_field,  Ingredients.C_field, Ingredients.Tmelt_field, Ingredients.KLT_field, Composit_Rec.Mass_PHR " 
        recipy_full=cur.execute("select " +fields+ "  from Composit_Descr, Ingredients, Composit_Rec where Composit_Descr.Composition_ID=Composit_Rec.Composition_ID and Ingredients.Ingr_ID=Composit_Rec.Ingr_ID and Composit_Rec.Composition_ID = " + str(rec_ID))        
        rec_lst = []
        for row in recipy_full:
            rec_lst.append(list(row))
        return(rec_lst)    

    def edit_composition(rec_ID): 
        fields = "Composit_Descr.Composition_Name, Composit_Descr.Composition_Descr, Ingredients.Ingr_Name, Composit_Rec.Mass_PHR, Composit_Rec.Ingr_ID " 
        recipy=cur.execute("select " +fields+ "  from Composit_Descr, Ingredients, Composit_Rec where Composit_Descr.Composition_ID=Composit_Rec.Composition_ID and Ingredients.Ingr_ID=Composit_Rec.Ingr_ID and Composit_Rec.Composition_ID = " + str(rec_ID))
        rec_lst = []
        for row in recipy:
            rec_lst.append(list(row))
        recipy=[]
        for i in range(len(rec_lst)):
            recipy.append(rec_lst[i][2:])
        layout = [  
                   [sg.Text('Отредактировать наименование/описание:', justification='с', text_color = 'red', font = ('bold'))],
                   [sg.Text('Наименование', justification='r', size=(13,1)),
              sg.Input(size=(13,1),do_not_clear=True, key='-Name-', default_text = rec_lst[0][0])],
              [sg.Text('Описание', justification='r', size=(13,1)),
              sg.Input(size=(35,1),do_not_clear=True, key='-Descr-', default_text = rec_lst[0][1])],
              [sg.Text('Отредактировать состав:', justification='с', text_color = 'red', font = ('bold'))]
              ]
        for i in range(len(recipy)):
            layout.append([
                        sg.Text(recipy[i][0], justification='l', size=(55,1)),
                        sg.Input(size=(5,1),do_not_clear=True, key='-Comp'+str(i)+'-',default_text = recipy[i][1])])              
        layout.append([ sg.B('Принять'),sg.B('Выход')]) 
 
        window = sg.Window('Композиции', layout,finalize=True)
        while True:
            event, values = window.read()
            if event in (None, 'Exit', 'Выход'):
                break
            if event == 'Принять':
                error = False
                Sum_ingr=0
                for i in range(len(rec_lst)):
                    rec_lst[i][0]=values['-Name-']
                    rec_lst[i][1]=values['-Descr-']
                    try:
                        rec_lst[i][3]=float(values['-Comp'+str(i)+'-'])
                        Sum_ingr += rec_lst[i][3]
                    except:
                        sg.popup('Данные не корректны!')
                        error = True
                        break
                if(int(Sum_ingr) != 100):
                    sg.popup('Сумма мас.% должна быть 100!')
                    error = True             
                if error == False:
                    cur.execute('update Composit_Descr SET Composition_Name = "'+rec_lst[0][0]+'", Composition_Descr = "'+rec_lst[0][1]+'" WHERE Composition_ID = '+ str(rec_ID))
                    for i in range(len(rec_lst)):
                        cur.execute('update Composit_Rec SET Mass_PHR = '+str(rec_lst[i][3])+' WHERE Composition_ID = '+ str(rec_ID)+' AND Composit_Rec.Ingr_ID = '+str(rec_lst[i][4]))
                    conn.commit()
                    sg.popup('Изменения внесены')                    
        window.close()                     

    def new_composition():
        ingreds = cur.execute("select Ingr_ID, Ingr_Name from Ingredients") 
        ing_lst = []
        for row in ingreds:
            ing_lst.append(list(row))
        ing_headings = ['ID','Наименование'] 
        recipy_lst = []
        layout = [  
                   [sg.Text('Создайте наименование/описание:', justification='с', text_color = 'red', font = ('bold'))],
                   [sg.Text('Наименование', justification='r', size=(13,1)),
              sg.Input(size=(13,1),do_not_clear=True, key='-Name-')],
              [sg.Text('Описание', justification='r', size=(13,1)),
              sg.Input(size=(35,1),do_not_clear=True, key='-Descr-')],
              [sg.Text('Выделите компонент:', justification='с', text_color = 'red', font = ('bold'))]
              ]
        layout.append([sg.Table(values=ing_lst,
                      headings=ing_headings,
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE1-')       
                      ])
        layout.append([sg.Text('Введите содержание, мас.%:', justification='l', size=(30,1),text_color = 'red', font = ('bold')),
                      sg.Input(size=(6,1),do_not_clear=False, key='-PHR-'),sg.B('Добавить компонент'),sg.B('Очистить')
                      ])
        layout.append([sg.Table(values=[['    ','                      ','    ']],
                      headings=['ID','Наименование','Мас.%.'],
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE2-')
        
                      ])                                    
        layout.append([ sg.B('Принять композицию'),sg.B('Выход')])                   
        window = sg.Window('Новая композиция', layout,finalize=True)
        while True:
            event, values = window.read()
            if event in (None, 'Exit', 'Выход'):
                break   
            if event == 'Добавить компонент':
                recipy_row = ing_lst[values['-TABLE1-'][0]]
                if values['-PHR-']:
                    try:
                        phr = float(values['-PHR-'])
                        recipy_row.append(phr)
                        recipy_lst.append(recipy_row)
                        window['-TABLE2-'].update(values=recipy_lst)
                        window.refresh()
                    except: 
                        sg.popup('Данные не корректны!')
            if event == 'Очистить':
                recipy_lst = []
                window['-TABLE2-'].update(values=recipy_lst)
                recipy_row =[]
                ing_lst = []
                ingreds = cur.execute("select Ingr_ID, Ingr_Name from Ingredients")
                for row in ingreds:
                    ing_lst.append(list(row))
                window.refresh()                      
            if event == 'Принять композицию':
                error = False
                if not (values['-Name-'] and values['-Descr-']):
                    sg.popup('Поля не должны быть пустыми!')
                    error = True
                elif recipy_lst == []:
                    sg.popup('Нужно создать рецепт!')
                    error = True
                Sum_ingr=0
                for i in range(len(recipy_lst)):
                    Sum_ingr += recipy_lst[i][2]
                if (int(Sum_ingr) != 100):
                    sg.popup('Сумма мас.% должна быть 100!')
                    error = True
                if error == False:
                    try:
                        insert_Name=cur.execute('INSERT INTO Composit_Descr (Composition_Name, Composition_Descr) Values ("'+values['-Name-']+'", "'+values['-Descr-']+'")')
                    except: 
                        sg.popup('Название должно быть уникальным!')
                        insert_Name = None
                    if insert_Name is not None:
                        conn.commit()
                        dic_table = get_data(conn,"Composit_Descr")
                        lastID = dic_table['data'][-1][0]
                        for i in range(len(recipy_lst)):
                            cur.execute('INSERT INTO Composit_Rec (Composition_ID, Ingr_ID, Mass_PHR) Values ('+str(lastID)+', '+str(recipy_lst[i][0])+', '+str(recipy_lst[i][2])+')')
                        conn.commit()
                        sg.popup('Запись добавлена')
                        break
        window.close() 
    
    def fractions_choose(recipy):
        recipy0=copy.deepcopy(recipy)
        recipy_lst = []
        results=''
        ing_headings = ['Компонент','Масс.%']
        Fract_headings = ['Компонент','Масс.%','d_min','d_max','d_melt','S_fact']
        layout = [
            [sg.Text('Параметр n кривой Фуллера: ', justification='r', size=(27,1)),
              sg.Input(size=(6,1),do_not_clear=True, key='-Fuller_n-', default_text = "0.5")],
            [sg.Text('Выбрана композиция: ', justification='l', size=(27,1))],
            [sg.Table(values=recipy,
                      headings=ing_headings,
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE1-')       
                      ],
            [sg.Text('Для каждого компонента введите параметры фракционного состава', justification='l', size=(62,1))],
            [sg.Text('Минимальный размер фракции, мкм:', justification='r', size=(50,1)),
              sg.Input(size=(6,1),do_not_clear=True, key='-d_min-')],
            [sg.Text('Максимальный размер фракции, мкм:', justification='r', size=(50,1)),
              sg.Input(size=(6,1),do_not_clear=True, key='-d_max-')],
            [sg.Text('Максимальный размер расплавленных частиц, мкм:', justification='r', size=(50,1)),
              sg.Input(size=(6,1),do_not_clear=True, key='-d_melt-')],
            [sg.Text('Фактор формы частиц: ', justification='r', size=(27,1)),
              sg.Input(size=(6,1),do_not_clear=True, key='-S_fact-', default_text = "1.0")],
            [sg.B('Добавить компонент'),sg.B('Очистить')],
            [sg.Table(values=[['        ','     ','     ','     ','      ','      ']],
                      headings=Fract_headings,
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE2-')
                      ],

            [sg.B('Принять'),sg.B('Выход')]    
        ]
        window = sg.Window('Моделирование фракционного состава', layout,finalize=True)
        while True:
            event, values = window.read()
            if event in (None, 'Exit', 'Выход'):
                break
            if event == 'Добавить компонент':
                if values['-TABLE1-']:
                    fraction_row = recipy[values['-TABLE1-'][0]]
                    fraction_keys = ['-d_min-','-d_max-','-d_melt-','-S_fact-']
                    error = False
                    for fr_key in fraction_keys:
                        if values[fr_key]:
                            try:
                                fr_val = float(values[fr_key])
                                fraction_row.append(fr_val)
                            except: 
                                sg.popup('Данные не корректны!')
                                error = True
                    if error == False:    
                        recipy_lst.append(fraction_row)
                        window['-TABLE2-'].update(values=recipy_lst)
                        window.refresh()
            if event == 'Очистить':
                recipy_lst = []
                fraction_row =[]
                window['-TABLE2-'].update(values=recipy_lst)
                window.refresh()
                recipy = copy.deepcopy(recipy0)
            if event == 'Принять':
                def Fuller(n, d_i, d_max):  
                    return ((d_i/d_max)**n)
                def FullerInv(phi,n,d_max,len_dsp=100):
                    d_space=np.linspace(0,d_max,len_dsp)
                    y_F=[Fuller(n, d_i, d_max) for d_i in d_space]
                    for i in reversed(range(len_dsp)):
                        if (y_F[i]<=1-phi):
                            return(d_space[i])
                def Unidistr(d_i, phi,d_min,d_max,K_sf):
                    if d_i<d_min:
                        return(0.)
                    if d_i>d_max:     
                        return(phi)
                    else:
                        return(phi*((d_i-d_min)/(d_max-d_min)*K_sf+1-K_sf))
                def R2f(Yth,Yex):
                    S2 = sum([(Yth[j]-Yex[j])**2 for j in range(len(Yth))])
                    S2mean = sum([(np.mean(Yth)-Yex[j])**2 for j in range(len(Yth))])    
                    return(1 - S2/S2mean)

                N_space=100 #Количество точек распределения
                if len(recipy_lst)==len(recipy0):
                    Particles = {}
                    for i in range(len(recipy_lst)):
                        ingr_Name = recipy_lst[i][0]
                        Ingrho = cur.execute("select Ingredients.rho_field from Ingredients where Ingr_Name = "+"'"+ingr_Name+"'")
                        Particles[ingr_Name] = [recipy_lst[i][1],[recipy_lst[i][2],recipy_lst[i][3],recipy_lst[i][4],recipy_lst[i][5]],[list(Ingrho)[0][0]]]
                    n_Fuller=float(values['-Fuller_n-'])
                    d_max = 1.
                    Vtot=0.
                    Vi = []
                    partkeys=[]
                    for key in Particles.keys():
                        partkeys.append(key)
                        d_max_i=Particles[key][1][1]
                        d_max = max(d_max_i,d_max)
                        Vii = Particles[key][0]/Particles[key][2][0]
                        Vtot += Vii
                        Vi.append(Vii)
                    d_space=np.linspace(0,d_max,N_space)
                    len_dsp=len(d_space)
                    y_Fn = []
                    y_part =[]
                    for d_i in d_space:
                        y_Fn.append(Fuller(n_Fuller, d_i, d_max))
                        y_p=0.
                        i=0
                        for key in Particles.keys():
                            phi_V = Vi[i]/Vtot
                            i += 1
                            if (Particles[key][1][2]<Particles[key][1][0]):
                                y_p += Unidistr(d_i, phi_V, Particles[key][1][0], Particles[key][1][1],Particles[key][1][-1])
                            else:
                                phi_melt = phi_V*(Particles[key][1][2]-Particles[key][1][0])/(Particles[key][1][1]-Particles[key][1][0])
                                y_p += Unidistr(d_i, phi_V*(1.-phi_melt),Particles[key][1][0],Particles[key][1][1],Particles[key][1][-1])
                                y_p += Unidistr(d_i, phi_V*phi_melt,0.,Particles[key][1][0],1.0)    
                        y_part.append(y_p)

                    phi_Vi=[]
                    for i in range(len(partkeys)):
                        phi_Vi.append(Vi[i]/Vtot)
                    Prt_dmax={}
                    Phi_i=0

                    for i in range(len(partkeys)):
                        d_max_i=Particles[partkeys[i]][1][1]
                        if (d_max_i>=d_max):
                            d_max = d_max_i
                            id_max=i
                            key_max_i = partkeys[i]
                    Phi_i = Phi_i + phi_Vi[id_max]
                    d_new = int(FullerInv(Phi_i,n_Fuller,d_max)) 
                    Prt_dmax[partkeys[id_max]] = [phi_Vi[id_max],[d_new,d_max]]
                    partkeys.remove(partkeys[id_max])
                    phi_Vi.remove(phi_Vi[id_max])
                    for i in range(len(partkeys)-1):
                        d_max_i = d_new
                        Phi_i = Phi_i + phi_Vi[i]
                        d_new = int(FullerInv(Phi_i,n_Fuller,d_max_i))
                        Prt_dmax[partkeys[i]] = [phi_Vi[i],[d_new,d_max_i]]
                    Prt_dmax[partkeys[-1]] = [phi_Vi[-1],[1,d_new]]
                    y_partOpt =[]
                    for d_i in d_space:
                        y_p=0.
                        i=0
                        for key in Prt_dmax.keys():
                            i += 1
                            y_p += Unidistr(d_i, Prt_dmax[key][0], Prt_dmax[key][1][0], Prt_dmax[key][1][1],1.0)
                        y_partOpt.append(y_p) 
                    R2=R2f(y_Fn,y_part)
                    R2_opt=R2f(y_Fn,y_partOpt)
                    results='Фракционный состав композиции: \n'
                    for key in Particles.keys():
                        results += (str(key)+' '+ str(Particles[key][0])+ '%, Размеры: '+ str(Particles[key][1][:-1])+ ' мкм, фактор формы = '
                        + str(Particles[key][1][-1]) +'\n')
                    results += 'Параметр n теоретического распределения: ' + str(n_Fuller) + '\n'
                    results += 'Близость к теоретическому распределению R2,% '+ str(int(R2*100)) + '\n'
                    results += 'Рациональный вариант фракционного состава: \n'
                    for key in Prt_dmax.keys():
                        results += (str(key)+' '+ ', Размеры: '+ str(Prt_dmax[key][1])+ ' мкм' +'\n')
                    results += 'Близость к теоретическому распределению R2,% '+ str(int(R2_opt*100)) + '\n'+ '\n'
                    print(results) 
                    plt.plot(d_space,y_Fn,'-ro',d_space,y_part,'c',d_space,y_partOpt,'m')
                    plt.show(block=False)
                    break
        window.close()
        return(results) 
  
               
    rec_ID = 1
    recipy_headings = ['Компонент','Мас.%.']
    rec_lst = recipy_choose(rec_ID)    
    layout = [
              [sg.Text('Выбрать существующую композицию:', justification='с')],
              [sg.Table(values=compositions,
                      headings=compositions_headings,
                      justification='r',
                      display_row_numbers=False,
                      num_rows=10,
                      key='-TABLE1-',
                      enable_events = True),
               sg.Table(values=rec_lst,
                      headings=recipy_headings,
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE2-')       
                      ],
              [ sg.B('Редактировать'), sg.B('Удалить'), sg.B('Создать'),sg.B('Обновить'),sg.B('Выход')],
              [sg.B('Фракционный состав'),sg.B('Теплофизические свойства')]       
              ]
    window = sg.Window('Композиции', layout,finalize=True)
    while True:
        event, values = window.read()
        if event == '-TABLE1-':
            window['-TABLE2-'].update(values=recipy_choose(compositions[values['-TABLE1-'][0]][0]))
            window.refresh()
        if event in (None, 'Exit', 'Выход'):
            break
        if event == 'Фракционный состав':
            if values['-TABLE1-']:
                recipy=recipy_choose(compositions[values['-TABLE1-'][0]][0])               
                results += fractions_choose(recipy)
        if event == 'Теплофизические свойства':
            if values['-TABLE1-']:
                recipy=recipy_choose(compositions[values['-TABLE1-'][0]][0])
                to_print = 'Состав композиции ' + compositions[values['-TABLE1-'][0]][1] + ':' 
                results += to_print+'\n'
                print(to_print)
                for i in range(len(recipy)):
                    to_print = recipy[i][0] + '  ' + str(recipy[i][1])
                    results += to_print+'\n'                  
                    print(to_print)    
                rec_lst=composition_choose(compositions[values['-TABLE1-'][0]][0])
                TotVol=0
                Vols=[]
                for i in range(len(rec_lst)):
                    Vols.append(rec_lst[i][-1]/rec_lst[i][3])
                    TotVol += Vols[i]
                for i in range(len(rec_lst)):
                    rec_lst[i].append(Vols[i]/TotVol)       
                Rho=0
                for i in range(len(rec_lst)):
                    Rho += rec_lst[i][-1]*rec_lst[i][3]    
                HV=0
                for i in range(len(rec_lst)):
                    HV += rec_lst[i][-1]*rec_lst[i][4]                               
                Lam=0
                for i in range(len(rec_lst)):
                    Lam += rec_lst[i][-1]*rec_lst[i][5] 
                Cp=0
                for i in range(len(rec_lst)):
                    Cp += rec_lst[i][-1]*rec_lst[i][6]                                  
                to_print = 'Результаты расчета теплофизических свойств:'      
                print(to_print)
                results += to_print+'\n'
                to_print = 'Плотность, кг/м^3   ' +  str(round(Rho,0))
                results += to_print+'\n'
                print(to_print)
                to_print = 'Твердость, HV        ' + str(round(HV,3))
                results += to_print+'\n'
                print(to_print) 
                to_print = 'Коэффициент теплопроводности, Вт/(м*К)  '+str(round(Lam,3))
                results += to_print+'\n'
                print(to_print)
                to_print = 'Теплоемкость, Дж/кг*К   ' +  str(round(Cp,2))+'\n'
                results += to_print+'\n'
                print(to_print)                                               
                window['-TABLE2-'].update(values=recipy_choose(compositions[values['-TABLE1-'][0]][0]))
                window.refresh()
        if event == 'Редактировать':
            if values['-TABLE1-']:
                edit_composition(compositions[values['-TABLE1-'][0]][0])
                window.refresh()
        if event == 'Создать':
            new_composition()
        if event == 'Удалить':
            if values['-TABLE1-']:
                rec_ID = compositions[values['-TABLE1-'][0]][0]
                sql_stm ='DELETE FROM ' +'Composit_Descr'+ ' WHERE Composition_ID=' +str(rec_ID) 
                cur.execute(sql_stm)
                cur.execute("PRAGMA foreign_keys =ON")
                conn.commit()
                table = 'Composit_Descr'
                sql_stm = "SELECT Composition_ID, Composition_Name, Composition_Descr FROM "+table
                cur.execute(sql_stm)
                compositions = cur.fetchall()
                window['-TABLE1-'].update(values=compositions)
                window['-TABLE2-'].update(values=['        ','     '])
                window.refresh() 
        if event == 'Обновить': 
            cur.execute('SELECT Composition_ID, Composition_Name, Composition_Descr FROM Composit_Descr')
            compositions = cur.fetchall()
            if values['-TABLE1-']: 
                window['-TABLE1-'].update(values=compositions)
                window['-TABLE2-'].update(values=recipy_choose(compositions[values['-TABLE1-'][0]][0]))       
    window.close()
    return(results)            

def ingredients_window():
    conn = db.connect(database=DBfilename)
    cur = conn.cursor()

    def edit_ingred(record):
        values_list=['-rho_field-','-HV_field-','-lamb_field-','-C_field-','-Tmelt_field-','-KLT_field-']
        types_list=['Металл','Оксид','Нитрид','Композит','Карбид' ]
        layout = [
                  [sg.Text('Отредактируйте поля:', justification='с')],
                  [sg.Text('Наименование', justification='r', size=(13,1)),
                    sg.Input(size=(80,1),do_not_clear=True, key='-Name-',default_text = record[1])],
                  [sg.Text('Тип', justification='r', size=(13,1)),
                    sg.Combo(types_list, default_value=[record[2]], size=(20,1), enable_events=True, key='-Type-')],
                  [sg.Text('Плотность, кг/м3', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-rho_field-',default_text = record[3])],
                  [sg.Text('Твердость, HV', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-HV_field-',default_text = record[4])],
                  [sg.Text('Теплопроводность, Вт/(м*К)', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-lamb_field-',default_text = record[5])],
                  [sg.Text('Теплоемкость, Дж/(кг*К)', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-C_field-',default_text = record[6])],
                  [sg.Text('Температура плавления, оС', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Tmelt_field-',default_text = record[7])],
                  [sg.Text('Коэфф. лин. расшир., К^-1*10^6', justification='r', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-KLT_field-',default_text = record[8])],
                  [ sg.B('Изменить запись'),sg.B('Добавить запись'),sg.B('Выход')] 
                 ]
        window = sg.Window('Компонент', layout,finalize=True)
        while True:
            event, values = window.read()
            if event in (None, 'Exit', 'Выход'):
                break
            if event == 'Изменить запись':
                error = False
                for val in values_list:
                    try:
                        float(values[val])
                    except:
                        sg.popup('Данные не корректны!')
                        error = True
                        break
                if error == False:
                    cur.execute(
                'update Ingredients SET '+
                'Ingr_Name = "'+values['-Name-']+'",'+
                'Ingr_Descr = "'+values['-Type-']+'",'+
                'rho_field ='+str(values['-rho_field-'])+','+
                'HV_field ='+str(values['-HV_field-'])+','+
                'lamb_field ='+str(values['-lamb_field-'])+','+
                'C_field ='+str(values['-C_field-'])+','+ 
                'Tmelt_field ='+str(values['-Tmelt_field-'])+','+                                
                'KLT_field ='+str(values['-KLT_field-'])+' '+               
                'WHERE Ingr_ID = '+ str(record[0]))
                    conn.commit()                 
                    sg.popup('Изменения внесены')
            if event == 'Добавить запись':
                error = False
                for i in range(len(values_list)):
                    try:
                        float(values[values_list[i]])
                    except:
                        sg.popup('Данные не корректны!')
                        error = True
                        break
                if error == False:
                    sql_stm = ('INSERT INTO Ingredients (Ingr_Name, Ingr_Descr, rho_field, HV_field, lamb_field, C_field, Tmelt_field, KLT_field ) Values ("'+
                    values['-Name-']+'","'+
                    values['-Type-']+'",'+
                    str(values['-rho_field-'])+','+
                    str(values['-HV_field-'])+','+
                    str(values['-lamb_field-'])+','+
                    str(values['-C_field-'])+','+ 
                    str(values['-Tmelt_field-'])+','+                                
                    str(values['-KLT_field-'])+')')
                    try:
                        cur.execute(sql_stm)
                        conn.commit()                 
                        sg.popup('Изменения внесены')
                    except:
                        sg.popup('Данные не корректны!')
                        error = True
                        break
        window.close()                     
                                     

    table = 'Ingredients'
    sql_stm = "SELECT * FROM "+table
    cur.execute(sql_stm)
    ingreds = cur.fetchall()
    ingreds_headings = ['ID','Наименование','Тип','Плотность, кг/м3','Твердость, HV', 'Lamba, Вт/(м*К)',  'Cp, Дж/кг*К','Tпл, оС','КЛТР, К^-1*10^6' ]
    layout = [
             [sg.Text('Компоненты', justification='с')],
             [sg.Table(values=ingreds,
                      headings=ingreds_headings,
                      justification='r',
                      display_row_numbers=False,
                      auto_size_columns = False,
                      col_widths =[4,15,8,10,10,10,10,10,12],
                      num_rows=20,
                      key='-TABLE1-',
                      enable_events = True),
                      ],
             [sg.B('Редактировать/Добавить'),sg.B('Удалить'),sg.B('Обновить'),sg.B('Выход')]
             ]
    window = sg.Window('Ингредиенты', layout,finalize=True)
    while True:
        event, values = window.read()
        if event == 'Редактировать/Добавить':
            if values['-TABLE1-']:
                edit_ingred(ingreds[values['-TABLE1-'][0]])
                window.refresh()            
        if event in (None, 'Exit', 'Выход'):
            break
        if event == 'Удалить':
            if values['-TABLE1-']:
                rec_ID = ingreds[values['-TABLE1-'][0]][0]
                sql_stm ='DELETE FROM ' +'Ingredients'+ ' WHERE Ingr_ID=' +str(rec_ID) 
                cur.execute(sql_stm)
                conn.commit()
                sg.popup('Запись удалена')
        if event == 'Обновить':
            cur.execute('SELECT * FROM Ingredients')
            ingreds = cur.fetchall() 
            window['-TABLE1-'].update(values=ingreds)                      

    window.close()
    
def optimize_window():
    from scipy.optimize import linprog
    conn = db.connect(database=DBfilename)
    cur = conn.cursor()
    ingreds = cur.execute("select Ingr_Name,rho_field,HV_field,lamb_field,C_field,Tmelt_field,KLT_field from Ingredients") 
    ing_lst=[]
    for row in ingreds:
        ing_lst.append(list(row))

    head_table1=['Наименование','Плот,кг/м3','Тверд,HV', 'Lam,Вт/(мК)','Cp,Дж/кгК','Tпл,оС','КЛТР*10^6']
    components=[]
    prop_lst = ['Плотн.,кг/м3','Тверд.,HV', 'Lamba,Вт/(м*К)','Cp,Дж/кг*К','Tпл,оС','КЛТР,К^-1*10^6']

    layout = [
        [sg.Text('Выделите компонент:', justification='с', text_color = 'red', font = ('bold'))],
             [sg.Table(values=ing_lst,
                      headings=head_table1,
                      justification='r',
                      display_row_numbers=False,
                      auto_size_columns = False,
                      col_widths =[15,8,8,10,8,8,10],
                      num_rows=5,
                      key='-TABLE1-',
                      enable_events = True),
                      ],
         [ sg.B('Добавить компонент'),sg.B('Очистить')],
         [sg.Text('Выбраны компоненты:', justification='с', text_color = 'red', font = ('bold'))],
         [sg.Table(values=[['                      ']],
                      headings=['Наименование'],num_rows=5,
                      justification='l',
                      display_row_numbers=False,
                      key='-TABLE2-')
                      ],
         [sg.Text('Выберите целевую функцию:', justification='с', text_color = 'red', font = ('bold'))],
         [sg.Listbox(size=(20,1),values= prop_lst, key='-Criterion-',default_values = ''),
         sg.Radio(text='минимум',group_id='R1', key='-min-',default = True),sg.Radio(text='максимум',group_id='R1', key='-max-')],
         [sg.Text('Добавьте ограничения:         >=                         <=', justification='с', text_color = 'red', font = ('bold'))],
         [sg.Text('Плотность, кг/м3, не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-rho>=-',default_text ='100' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-rho<=-',default_text = '10000')
                      ],
         [sg.Text('Твердость,HV, не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-HV>=-',default_text ='100' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-HV<=-',default_text = '10000')
                      ],
         [sg.Text('Lamda,Вт/(м К), не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Lamb>=-',default_text ='1' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Lamb<=-',default_text = '100')
                      ],
         [sg.Text('Cp,Дж/(кг К), не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Cp>=-',default_text ='1' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Cp<=-',default_text = '1000')
                      ],
         [sg.Text('Tпл,оС, не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Tmelt>=-',default_text ='1' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-Tmelt<=-',default_text = '10000')
                      ],
         [sg.Text('КЛТР*10^6, не меньше:', justification='с', size=(33,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-KLT>=-',default_text ='1' ),
                    sg.Text('не больше:', justification='с', size=(15,1)),
                    sg.Input(size=(6,1),do_not_clear=True, key='-KLT<=-',default_text = '100')
                      ],

         [sg.B('Решить'),sg.B('Выход')]                         
    
    ]
    key_list=['-rho>=-','-rho<=-','-HV>=-','-HV<=-','-Lamb>=-','-Lamb<=-','-Cp>=-','-Cp<=-','-Tmelt>=-','-Tmelt<=-','-KLT>=-','-KLT<=-']
    window = sg.Window('Оптимизация состава композиции', layout,finalize=True)
    while True:
        event, values = window.read()
        if event in (None, 'Exit', 'Выход'):
            break   
        if event == 'Добавить компонент':
            components_row = ing_lst[values['-TABLE1-'][0]]
            components.append(components_row)
            window['-TABLE2-'].update(values=components)
            window.refresh()
        if event == 'Очистить':
            components=[]
            window['-TABLE2-'].update(values=['    ','                      '])
            window.refresh()
        if event == 'Решить':
            if len(components)>1:
                if (values['-Criterion-'] != []):
                    obj = []
                    
                    choosed_propID=prop_lst.index(values['-Criterion-'][0])
                    if (values['-min-']):
                        choosed_opt = 'минимум'
                        for i in range(len(components)):
                            obj.append(components[i][1+choosed_propID])
                    elif (values['-max-']):
                        choosed_opt = 'максимум'
                        for i in range(len(components)):
                            obj.append(components[i][1+choosed_propID]*-1.)
                    lhs_ineq = []
                    rhs_ineq = []
                    lhs_eq =[]
                    lhs_eq_i =[]
                    bnd = []
                    for i in range(6):
                        prop_less_i=[]
                        prop_more_i=[]
                        for j in range(len(components)):
                            prop_less_i.append(components[j][i+1])
                            prop_more_i.append(components[j][i+1]*-1.)
                        lhs_ineq.append(prop_more_i)
                        lhs_ineq.append(prop_less_i)
                    for i in range(len(key_list)):
                        if i%2==0:
                            rhs_ineq.append(float(values[key_list[i]])*-1.)
                        else: rhs_ineq.append(values[key_list[i]])
                    for i in range(len(components)):
                        lhs_eq_i.append(1)
                    lhs_eq.append(lhs_eq_i)
                    rhs_eq = [1] 

                    for i in range(len(components)):
                        bnd.append((0, float("inf")))
                        
                    print('Выбраны компоненты:')
                    for i in range(len(components)):
                        print(components[i][0])
                        
                    print('\nРешение задачи оптимизации')
                    print('Целевая функция:')
                    print(values['-Criterion-'],obj)
                    print('Вид поиска: ',choosed_opt)
                    print('Параметры ограничений:')
                    print(lhs_ineq)
                    print(rhs_ineq)
                    print(lhs_eq)
                    print(bnd)
                    
                    opt = linprog(c=obj, A_ub=lhs_ineq, b_ub=rhs_ineq,
                            A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd)
                    print('Результаты решения:')
                    if (opt.success == True):

                        print('Решение найдено')
                        #print('Объемные доли компонентов в точке оптимума:')
                        #for i in range(len(components)):
                        #    print(components[i][0],' ',round(float(opt.x[i]),3))
                        print('Массовые доли компонентов в точке оптимума:')
                        Tot_phiM=sum([components[i][1]*float(opt.x[i]) for i in range(len(components))])
                        for i in range(len(components)):
                            print(components[i][0],' ',round(components[i][1]*float(opt.x[i])/Tot_phiM,3))
                        if (choosed_opt == 'минимум'):
                            print('Значение функции в точке минимума: ', round(float(opt.fun),3))
                        elif (choosed_opt == 'максимум'):
                            print('Значение функции в точке максимума: ', round(float(opt.fun),3)*-1.)
                    else:
                        print('Решение не найдено. Проверьте функцию и ограничения')
                    
                else: sg.popup('Выберите целевую функцию')
             
            
    window.close() 

    

def main_window():
    howto = '''
            Введите свойства компонентов композиции с помощью пункта "Ингредиенты" в меню "Базы данных".
            В пункте "Композиции" меню "База данных" выделите и отредактируйте имеющуюся композицию
            или создайте новую с помощью кнопок "Редактировать" и "Создать".
            Кнопка "Удалить" удаляет композицию из базы данных.
            Кнопка "Обновить" обновляет окно композиций после создания новой композиции. 
            При нажатии кнопки "Теплофизические свойства" для выделенной композиции будут расcчитаны 
            теплофизические свойства.
            Пункт "Фракционный состав" позволяет построить график оптимальной гранулометрической кривой.
            Пункт "Оптимизация" меню "Базы данных" позволяет провести оптимизацию состава композиции
            методом линейного программирования.
            Для сохранения результатов расчета в текстовом файле выберите в меню
            "Файл" пункт "Сохранить". 
            '''
    about = '''
            Программа расчета теплофизических характеристик металло-керамических композиций.
            Программа содержит 3 части - интерфейс, расчетный модуль и базу данных теплофизических характеристик.
            Расчет производится на основании "правила смесей", в соотвествии с которым значение
            выходного параметра композиции (плотность, теплоемкость, теплопроводность) рассчитывается
            как сумма данных параметров каждого компонента, умноженных на их объемные доли в смеси.
            ''' 
    about += Version + Developed
          
    sg.set_options(element_padding=(0, 0))        
    menu_def = [['Файл', ['Выбрать базу данных','Сохранить результат', 'Выход' ]],
                ['База данных', ['Ингредиенты','Композиции','Оптимизация' ]],
                ['Справка', ['Порядок расчета','О программе' ]]
                ]
    layout = [
              [sg.Menu(menu_def, tearoff=False, pad=(20,1))],
              [sg.Output(size=(110,20),key ='-Out-')],
              [sg.Cancel('Выход')],
              ]
    window = sg.Window("Расчет свойств металло-керамических композиций",
                       layout,
                       default_element_size=(12, 1),
                       grab_anywhere=True,
                       default_button_element_size=(12, 1))                       
    while True:
        event, values = window.read()
        if event in (None, 'Exit', 'Выход'):
            break
        if event == 'Выбрать базу данных':
            global DBfilename
            DBfilename = sg.popup_get_file('file to open', no_window=True)
            print('Выбран файл базы данных: \n',DBfilename)
        if event == 'Порядок расчета':
            sg.popup('Порядок расчета',howto,grab_anywhere=True)
        if event == 'О программе':
            sg.popup('О программе',about,grab_anywhere=True)            
        if event == 'Композиции':
            results=composition_window()
        if event == 'Ингредиенты':
            ingredients_window()
        if event == 'Оптимизация':
            optimize_window()
        if event == 'Сохранить результат':
            try:
                save_results(results)
            except:
                sg.popup('Окно пустое')
    window.close()

main_window()

