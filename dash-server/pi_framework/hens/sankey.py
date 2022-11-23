import plotly.graph_objects as go
import numpy as np

def plot_sankey_example():
    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = ["A1", "A2", "B1", "B2", "C1", "C2"],
            color = "blue"
        ),
        link = dict(
            source = [0, 1, 0, 2, 3, 3], # indices correspond to labels, eg A1, A2, A1, B1, ...
            target = [2, 3, 3, 4, 4, 5],
            value = [8, 4, 2, 8, 4, 2]
        ))])

    fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
    fig.show()

def plot_sankey(labels, data, title=None):

    link = dict(
        source = data['source'], # indices correspond to labels, eg A1, A2, A1, B1, ...
        target = data['target'],
        value = data['value'],
    )

    if 'color' in data.keys():
        link['color'] = data['color']

    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = labels,
            color = "black"
        ),
        link = link
    )])

    if title is None:
        title = "Basic Sankey Diagram"

    fig.update_layout(title_text=title, font_size=10)
    fig.show()


def prep_data_schnaitl(res, set_period):
    labels = []
    labels += list(res.unit.keys())
    labels += list(res.node.keys())

    def period_value(port, set_period):
        soc_ordered = []
        for i, n in enumerate(set_period):
            soc_ordered = np.concatenate([soc_ordered, list(port[n,:].value)])
        return soc_ordered

    basic_color = 'rgba(204,0,0, 0.4)'
    electricity_color = 'rgba(34,139,34, 0.4)'

    source = []
    target = []
    value = []
    color = []

    for node in res.node.keys():
        lhs = res.node[node].param['lhs']
        rhs = res.node[node].param['rhs']
        try:
            (len(lhs) == 1) and (len(rhs) == 1) and (res.node[node].param['type'] is '==')
        except:
            print('error')
        if (len(lhs) == 1) and (len(rhs) == 1) and (res.node[node].param['type'] is '=='):
            source += [labels.index(lhs[0][0])]
            target += [labels.index(rhs[0][0])]
            port = res.unit[lhs[0]].port[lhs[0][1]]
            value += [np.sum(period_value(port, set_period))]

            if 'el' in lhs[0][0]:
                color += [electricity_color]
            else:
                color += [basic_color]

        else:
            for i in lhs:
                source += [labels.index(i[0])]
                target += [labels.index(node)]
                # value += [np.sum(list(res.unit[i[0]].port[i[1]].get_values().values()))]
                port = res.unit[i[0]].port[i[1]]
                value += [np.sum(period_value(port, set_period))]

                if 'el' in lhs[0][0]:
                    color += [electricity_color]
                else:
                    color += [basic_color]

            for i in rhs:
                source += [labels.index(node)]
                target += [labels.index(i[0])]
                # value += [np.sum(list(res.unit[i[0]].port[i[1]].get_values().values()))]
                port = res.unit[i[0]].port[i[1]]
                value += [np.sum(period_value(port, set_period))]

                if 'el' in rhs[0][0]:
                    color += [electricity_color]
                else:
                    color += [basic_color]




    data = dict(
        source = source,
        target = target,
        value = value,
        color = color,
    )

    return labels, data

if __name__ == '__main__':
    plot_sankey_example()