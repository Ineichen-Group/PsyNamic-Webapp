var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.Tag = function (props) {
    const tags = props.value;

    // If no tags, return empty div
    if (!tags || tags.length === 0) {
        return React.createElement('div', {}); // Return an empty div if no tags
    }

    return React.createElement(
        'div',
        {
            style: {
                display: 'flex',
                alignItems: 'center',
                height: '100%',
            }
        },
        tags.map((tagData, index) => {
            const { task, label, color } = tagData;

            return React.createElement(
                'span',
                {
                    className: 'badge',
                    style: {
                        backgroundColor: color,
                        cursor: 'pointer',
                        padding: '8px 13px',  // Tag like appearance
                        marginRight: '5px',
                        borderRadius: '20px',
                        display: 'inline-block',
                        textAlign: 'center',
                    },
                    'data-toggle': 'tooltip',
                    'data-placement': 'top',
                    title: `${task}: ${label}`  // Tooltip
                },
                ''  // No text inside the tag itself
            );
        })
    );
};
